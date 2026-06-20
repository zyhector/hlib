import frontmatter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from flask import Flask, abort, render_template, request


@dataclass
class Novel:
    title: str | None = None
    author: str | None = None
    series: str | None = None
    series_index: int | None = None
    tags: list | None = None
    link: str | None = None
    upload_time: date | None = None
    content: str | None = None


def load_novel(path: Path) -> Novel:
    post = frontmatter.load(path)
    meta = post.metadata
    return Novel(
        title=meta.get("title"),
        author=meta.get("author"),
        series=meta.get("series"),
        series_index=meta.get("series_index"),
        tags=meta.get("tags"),
        link=meta.get("link"),
        upload_time=meta.get("upload_time"),
        content=post.content or None,
    )


def load_all(data_dir: Path) -> list[Novel]:
    return [load_novel(p) for p in data_dir.glob("**/*.txt")]


app = Flask(__name__)
novels: list[Novel] = sorted(load_all(Path("data")), key=lambda n: n.upload_time or date.min, reverse=True)


def filter_novels(author=None, series=None, tag=None) -> list[tuple[int, Novel]]:
    result = list(enumerate(novels))

    if author:
        result = [(i, n) for i, n in result if n.author == author]
    elif series:
        result = [(i, n) for i, n in result if n.series == series]
        result.sort(key=lambda x: x[1].series_index or 0)
    elif tag:
        result = [(i, n) for i, n in result if n.tags and tag in n.tags]

    return result


@app.get("/")
def index():
    return render_template("list.html", novels=enumerate(novels), filter_desc=None)


@app.get("/filter")
def filter_view():
    author = request.args.get("author")
    series = request.args.get("series")
    tag = request.args.get("tag")

    filtered = filter_novels(author=author, series=series, tag=tag)

    if author:
        filter_desc = f"作者：{author}"
    elif series:
        filter_desc = f"系列：{series}"
    elif tag:
        filter_desc = f"#{tag}"
    else:
        filter_desc = None

    return render_template("list.html", novels=filtered, filter_desc=filter_desc)


@app.get("/tags")
def tags():
    from collections import Counter
    counts = Counter(tag for n in novels if n.tags for tag in n.tags)
    items = [(f"#{name}", count, f"/filter?tag={name}") for name, count in counts.most_common()]
    return render_template("enum.html", title="标签", items=items)


@app.get("/authors")
def authors():
    from collections import Counter
    counts = Counter(n.author for n in novels if n.author)
    items = [(name, count, f"/filter?author={name}") for name, count in counts.most_common()]
    return render_template("enum.html", title="作者", items=items)


@app.get("/series")
def series():
    from collections import Counter
    counts = Counter(n.series for n in novels if n.series)
    items = [(name, count, f"/filter?series={name}") for name, count in counts.most_common()]
    return render_template("enum.html", title="系列", items=items)


@app.get("/novel/<int:i>")
def novel(i: int):
    if i >= len(novels):
        abort(404)
    return render_template("novel.html", novel=novels[i])


if __name__ == "__main__":
    app.run(debug=True)
