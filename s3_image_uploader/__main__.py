import os
from pathlib import Path
from typing import Optional

import click


from . import upload


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
@click.argument("TARGET", type=str)
def main(
    url: str, post_token: str, target: str, target_filename: Optional[str]
) -> None:
    if Path(target).resolve().absolute().exists():
        if target_filename is None:
            target_filename = os.path.basename(target)
            assert os.path.isfile(target)
        click.echo(
            upload(
                instance_url=url,
                post_token=post_token,
                target_filename=target_filename,
                file=target,
            )
        )
    else:
        assert target.startswith("http"), f"Not an HTTP url: {target}"
        if target_filename is None:
            target_filename = click.prompt("Target filename to upload to", type=str)
        assert target_filename is not None
        click.echo(
            upload(
                instance_url=url,
                post_token=post_token,
                target_filename=target_filename,
                url=target,
            )
        )


if __name__ == "__main__":
    main(prog_name="s3_image_uploader")
