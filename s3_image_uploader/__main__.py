import os
from pathlib import Path
from typing import Optional

import click


from . import upload_with_index


@click.command()
@click.option(
    "-u",
    "--url",
    envvar="INSTANCE_URL",
    help="url of hosted instance, e.g. at name.vercel.app",
    required=True,
)
@click.option(
    "-t",
    "--post-token",
    envvar="POST_TOKEN",
    help="Secret POST token",
    required=True,
)
@click.option(
    "-f",
    "--target-filename",
    help="path to upload image to",
    required=False,
    default=None,
)
@click.option(
    "--index/--no-index",
    default=False,
    help="index image to local index -- prevents duplicate uploads",
)
@click.argument("TARGET", type=str)
def main(
    url: str,
    post_token: str,
    target: str,
    target_filename: Optional[str],
    index: bool,
) -> None:
    remote_url: str
    if Path(target).resolve().absolute().exists():
        if target_filename is None:
            target_filename = os.path.basename(target)
            assert os.path.isfile(target)
        remote_url = upload_with_index(
            instance_url=url,
            post_token=post_token,
            target_filename=target_filename,
            file=target,
            index=index,
        )
    else:
        assert target.startswith("http"), f"Not an HTTP url: {target}"
        if target_filename is None:
            target_filename = click.prompt("Target filename to upload to", type=str)
        assert target_filename is not None
        remote_url = upload_with_index(
            instance_url=url,
            post_token=post_token,
            target_filename=target_filename,
            url=target,
            index=index,
        )

    click.echo(remote_url)

    try:
        import pyperclip  # type: ignore[import]

        pyperclip.copy(remote_url)
    except ImportError:
        pass


if __name__ == "__main__":
    main(prog_name="s3_image_uploader")
