import colorsys


def get_colored_text_by_rgb(r, g, b, text):
    if text is None:
        return ""

    return "\x1b[38;2;{};{};{}m{}\x1b[0m".format(r, g, b, text)


def get_colored_text_by_hsv(h, s, v, text):
    if text is None:
        return ""

    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    return get_colored_text_by_rgb(r, g, b, text)
