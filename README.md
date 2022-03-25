# s3-image-server

Modified from [`simonw/s3-image-proxy`](https://github.com/simonw/s3-image-proxy) to allow uploading images as well

[`starlette`](https://www.starlette.io/) application for uploading and retrieving image files from a private S3 bucket, resizing them based on querystring parameters and serving them with cache headers so the resized images can be cached by a CDN.

## Configuration

The following environment variables are required:

- `S3_BUCKET`
- `S3_AWS_ACCESS_KEY_ID`
- `S3_AWS_SECRET_ACCESS_KEY`
- `POST_TOKEN` - to authenticate, for uploading images

Here [are some notes](https://github.com/dogsheep/dogsheep-photos/issues/4) on creating an S3 bucket with the right credentials.

I personally, just:

- Created a S3 bucket with no public access
- Created an IAM user which has `AmazonS3FullAccess`

## Deployment

You can deploy this tool directly to [Vercel](https://vercel.com/). You'll need to set the necessary environment variables.

Vercel provides a CDN, so resized images should be served very quickly on subsequent requests to the same image.

## Local development

For local development you will need to install an additional dependency: uvicorn.

    pip install -r requirements.txt
    pip install uvicorn

You can then run the server like this:

    S3_AWS_ACCESS_KEY_ID="xxx" \
    S3_AWS_SECRET_ACCESS_KEY="yyy" \
    S3_BUCKET="your-bucket" \
    POST_TOKEN="your-secret-token" \
    uvicorn index:app

## Usage

Once up and running, you can access image files stored in the S3 bucket like so:

    http://localhost:8000/i/name-of-file.jpeg

To resize the image, pass ?w= or ?h= arguments:

    http://localhost:8000/i/name-of-file.jpeg?w=400
    http://localhost:8000/i/name-of-file.jpeg?h=400

Use `?bw=1` to convert the image to black and white.

If you are serving JPEGs you can control the quality using `?q=` - e.g. `?q=25` for a lower quality (but faster loading) image.

## Uploading Images

An example uploading a base64 encoded image:

`curl -sL -X POST localhost:8000/u/test.png -d '{"image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII==", "token": "secret_token"}' | jq`

To proxy a URL (request/download it, then re-host it):

`curl -sL -X POST localhost:8000/u/test2.png -d '{"url": "https://sean.fish/images/frontend/rubikscube.png", "token": "secret_token"}'`

To retrieve that, use: `localhost:8000/i/test.png`

## Library/CLI

Also includes a small CLI module/function that lets you upload, see [the upload function](./s3_image_uploader/__init__.py) for library usage, and from cli:

```
$ python3 -m s3_image_uploader --url http://localhost:8000 -t secret_token ~/Pictures/Sun/sun_painting.jpg
http://localhost:8000/i/sun_painting.jpg
```

(Can also set the `INSTANCE_URL` and `POST_TOKEN` environment variables instead of providing them as CLI arguments)

To install, run `pip install .` in the root directory, or:

```
pip install 'git+https://github.com/seanbreckenridge/s3-image-server'
```
