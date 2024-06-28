import pytest

from flickr_photos_api.types import get_machine_tags, MachineTags


@pytest.mark.parametrize(
    ["tags", "machine_tags"],
    [
        ([], {}),
        (["Natural history", "Periodicals", "Physical sciences"], {}),
        (
            [
                "Natural history",
                "Periodicals",
                "Physical sciences",
                "bhl:page=33665645",
            ],
            {"bhl:page": ["33665645"]},
        ),
        (
            [
                "Natural history",
                "Periodicals",
                "Physical sciences",
                "bhl:page=33665645",
                "taxonomy:genus=Loxodonta",
                "taxonomy:binomial=Elephas maximus",
                "taxonomy:binomial=Elephas indicus",
            ],
            {
                "bhl:page": ["33665645"],
                "taxonomy:genus": ["Loxodonta"],
                "taxonomy:binomial": ["Elephas maximus", "Elephas indicus"],
            },
        ),
    ],
)
def test_get_machine_tags(tags: list[str], machine_tags: MachineTags) -> None:
    assert get_machine_tags(tags) == machine_tags
