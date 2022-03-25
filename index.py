import io
import os
import secrets
import base64

import boto3  # type: ignore[import]
import httpx
import pyheif  # type: ignore[import]
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.requests import Request
from starlette.routing import Route
from PIL import Image, ExifTags  # type: ignore[import]

load_dotenv()


for ORIENTATION_TAG in ExifTags.TAGS.keys():
    if ExifTags.TAGS[ORIENTATION_TAG] == "Orientation":
        break


client = boto3.client(
    "s3",
    aws_access_key_id=os.environ["S3_AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["S3_AWS_SECRET_ACCESS_KEY"],
)

AWS_S3_BUCKET = os.environ["S3_BUCKET"]


def url_for_image(path, ext):
    key = "{}.{}".format(path, ext)
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": AWS_S3_BUCKET,
            "Key": key,
        },
        ExpiresIn=600,
    )


async def homepage(_: Request) -> Response:
    return JSONResponse(
        {"error": "Nothing to see here, use /i/ to fetch and /u/ to upload"}
    )


def media_format(ext: str) -> str:
    return "image/{}".format(ext.lower())


async def image(request: Request) -> Response:
    key = request.path_params["key"]
    path, _, ext = key.partition(".")
    if path.strip() == "":
        return JSONResponse({"error": "path param must not be empty"}, status_code=400)
    if ext.strip() == "":
        return JSONResponse(
            {"error": "extention for path must not be empty"}, status_code=400
        )

    url = url_for_image(path, ext)

    # Fetch original
    async with httpx.AsyncClient(verify=False) as client:
        image_response = await client.get(url)
    if image_response.status_code == 404:
        return JSONResponse(
            {"error": "image not found", "status_code": 404}, status_code=404
        )

    if image_response.status_code != 200:
        return JSONResponse(
            {
                "error": "Status code not 200",
                "status_code": image_response.status_code,
                "body": repr(image_response.content),
            }
        )

    # Load it into Pillow
    if ext == "heic":
        heic = pyheif.read_heif(image_response.content)
        image = Image.frombytes(mode=heic.mode, size=heic.size, data=heic.data)  # type: ignore
    else:
        image = Image.open(io.BytesIO(image_response.content))

    # Does EXIF tell us to rotate it?
    try:
        exif = dict(image._getexif().items())  # type: ignore
        if exif[ORIENTATION_TAG] == 3:
            image = image.rotate(180, expand=True)
        elif exif[ORIENTATION_TAG] == 6:
            image = image.rotate(270, expand=True)
        elif exif[ORIENTATION_TAG] == 8:
            image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass

    # Resize based on ?w= and ?h=, if set
    width, height = image.size
    w = request.query_params.get("w")
    h = request.query_params.get("h")
    if w is not None or h is not None:
        if h is None:
            # Set h based on w
            w = int(w)
            h = int((float(height) / width) * w)
        elif w is None:
            h = int(h)
            # Set w based on h
            w = int((float(width) / height) * h)
        w = int(w)
        h = int(h)
        image.thumbnail((w, h))

    # ?bw= converts to black and white
    if request.query_params.get("bw"):
        image = image.convert("L")

    # ?q= sets the quality - defaults to 75
    quality = 75
    q = request.query_params.get("q")
    if q and q.isdigit() and 1 <= int(q) <= 100:
        quality = int(q)

    # Output as JPEG or PNG
    output_image = io.BytesIO()
    image_type = "JPEG"
    kwargs = {"quality": quality}
    if image.format == "PNG":
        image_type = "PNG"
        kwargs = {}

    image.save(output_image, image_type, **kwargs)
    return Response(
        output_image.getvalue(),
        media_type=media_format(image_type),
        headers={"cache-control": "s-maxage={}, public".format(365 * 24 * 60 * 60)},
    )


async def upload(request: Request) -> Response:
    key = request.path_params["key"]
    body = await request.json()
    if not isinstance(body, dict):
        return JSONResponse({"error": "Body must be a JSON object"})

    if not body.get("token"):
        return JSONResponse({"error": "Missing token"})

    path, _, ext = key.partition(".")
    if path.strip() == "":
        return JSONResponse({"error": "path param must not be empty"}, status_code=400)
    if ext.strip() == "":
        return JSONResponse(
            {"error": "extention for path must not be empty"}, status_code=400
        )

    if not secrets.compare_digest(body["token"], os.environ["POST_TOKEN"]):
        return JSONResponse(
            {"error": "token body param mismatch"},
            status_code=403,
        )

    buf: io.BytesIO
    if "image" in body:
        if "," in body["image"]:
            # e.g. remove data:image/png;base64, from the beginning
            encoded = body["image"].split(",", maxsplit=1)[1]
        else:
            encoded = body["image"]
        try:
            buf = io.BytesIO(base64.b64decode(encoded))
        except TypeError:
            return JSONResponse(
                {"error": "image body param 'image' must be a base64 encoded image"},
                status_code=400,
            )
    elif "url" in body:
        async with httpx.AsyncClient() as url_client:
            image_response = await url_client.get(body["url"])
            if image_response.status_code != 200:
                return JSONResponse(
                    {
                        "error": "Status code not 200",
                        "status_code": image_response.status_code,
                        "body": repr(image_response.content),
                    },
                    status_code=400,
                )
            buf = io.BytesIO(image_response.content)
    else:
        return JSONResponse(
            {"error": "body param 'image' or 'url' must be set"}, status_code=400
        )

    # upload to aws s3
    client.upload_fileobj(
        buf,
        Bucket=AWS_S3_BUCKET,
        Key=key,
        ExtraArgs={"ContentType": media_format(ext)},
    )

    return JSONResponse({"status": "created"}, status_code=201)


app = Starlette(
    debug=bool(os.environ.get("DEBUG")),
    routes=[
        Route("/", homepage),
        Route("/i/{key}", image),
        Route("/u/{key}", upload, methods=["POST"]),
    ],
)
