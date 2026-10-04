"""Read container facts from a generated MP4 without external tools."""
import struct
import urllib.request

LIMIT = 80 * 1024 * 1024
CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl"}


def boxes(data, start, end):
    while start + 8 <= end:
        size, kind = struct.unpack(">I4s", data[start:start + 8])
        header = 8
        if size == 1:
            if start + 16 > end:
                return
            size = struct.unpack(">Q", data[start + 8:start + 16])[0]
            header = 16
        elif size == 0:
            size = end - start
        if size < header or start + size > end:
            return
        yield kind, start + header, start + size
        start += size


def find(data, start, end, kind):
    return next(((a, b) for k, a, b in boxes(data, start, end) if k == kind), None)


def track(data, start, end):
    info = {}
    header = find(data, start, end, b"tkhd")
    if header:
        a, b = header
        # Width and height are the last two 16.16 fixed-point fields.
        info["width"], info["height"] = (x >> 16 for x in struct.unpack(">II", data[b - 8:b]))
    media = find(data, start, end, b"mdia")
    if not media:
        return info
    handler = find(data, media[0], media[1], b"hdlr")
    if handler:
        info["handler"] = data[handler[0] + 8:handler[0] + 12].decode("latin-1")
    inner = media
    for kind in (b"minf", b"stbl", b"stsd"):
        inner = inner and find(data, inner[0], inner[1], kind)
    if inner and inner[1] - inner[0] >= 16:
        info["codec"] = data[inner[0] + 12:inner[0] + 16].decode("latin-1").strip()
    return info


def inspect(data):
    movie = find(data, 0, len(data), b"moov")
    if not movie:
        raise ValueError("No movie header; not a readable MP4")
    result = {"container": "mp4", "bytes": len(data), "has_audio": False, "audio_codec": None, "video_codec": None}
    header = find(data, movie[0], movie[1], b"mvhd")
    if header:
        a = header[0]
        if data[a] == 1:
            scale, length = struct.unpack(">IQ", data[a + 20:a + 32])
        else:
            scale, length = struct.unpack(">II", data[a + 12:a + 20])
        if scale:
            result["duration_seconds"] = round(length / scale, 6)
    for kind, a, b in boxes(data, movie[0], movie[1]):
        if kind != b"trak":
            continue
        info = track(data, a, b)
        if info.get("handler") == "soun":
            result["has_audio"] = True
            result["audio_codec"] = info.get("codec")
        elif info.get("handler") == "vide" and "width" not in result:
            result.update(width=info.get("width"), height=info.get("height"), video_codec=info.get("codec"))
    return result


def probe(url):
    """Never raises: a failed inspection is reported as unverified, not as a failed video."""
    try:
        if not url.startswith("https://"):
            raise ValueError("Only HTTPS media can be inspected")
        with urllib.request.urlopen(urllib.request.Request(url), timeout=90) as response:
            data = response.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError("Video exceeds the inspection size limit")
        return inspect(data)
    except Exception as error:
        return {"error": (type(error).__name__ + ": " + str(error).split("?")[0])[:200]}
