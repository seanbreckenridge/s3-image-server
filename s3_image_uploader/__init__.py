import os
import base64
from pathlib import Path
from typing import Optional, Union, Tuple

import httpx

PathIsh = Union[str, Path]


def from_env(instance_url: Optional[str], post_token: Optional[str]) -> Tuple[str, str]:
    if instance_url is None:
        instance_url = os.getenv("INSTANCE_URL")

    if instance_url is None:
        raise ValueError(
            "must pass instance_url or set INSTANCE_URL environment variable"
        )

    if post_token is None:
        post_token = os.getenv("POST_TOKEN")

    if post_token is None:
        raise ValueError("must pass post_token or set POST_TOKEN environment variable")

    return instance_url, post_token


def upload(
    *,
    target_filename: str,
    instance_url: Optional[str] = None,
    post_token: Optional[str] = None,
    url: Optional[str] = None,
    file: Optional[PathIsh] = None,
) -> str:
    if url is None and file is None:
        raise ValueError("Either url or file must be specified")
    if url is not None:
        data = {
            "url": url,
            "token": post_token,
        }
    else:
        assert file is not None
        file = Path(file)
        with open(file, "rb") as f:
            img_bytes = base64.b64encode(f.read())
        data = {
            "image": img_bytes.decode("utf-8"),
            "token": post_token,
        }

    instance_url, post_token = from_env(instance_url, post_token)

    resp = httpx.post(
        instance_url + f"/u/{target_filename}",
        json=data,
    )
    if resp.status_code != 201:
        raise RuntimeError(f"Failed to upload image: {resp.status_code} {resp.text}")

    return instance_url + f"/i/{target_filename}"


def upload_with_index(
    *,
    index: bool = True,
    target_filename: str,
    instance_url: Optional[str] = None,
    post_token: Optional[str] = None,
    url: Optional[str] = None,
    file: Optional[PathIsh] = None,
) -> str:
    instance_url, post_token = from_env(instance_url, post_token)
    from . import cache

    if not index:
        return upload(
            target_filename=target_filename,
            instance_url=instance_url,
            post_token=post_token,
            url=url,
            file=file,
        )
    else:
        # this assumes that the file hasnt been deleted
        if cache.has(target_filename):
            return instance_url + f"/i/{target_filename}"
        else:
            url = upload(
                target_filename=target_filename,
                instance_url=instance_url,
                post_token=post_token,
                url=url,
                file=file,
            )
            cache.add(target_filename)
            return url
