from PyQt5.QtGui import QFont, QFontMetrics


def ms_to_time(milliseconds):
    secs = int(milliseconds / 1000)
    mins = int(secs / 60)
    secs -= mins * 60
    hours = int(mins / 60)
    mins -= hours * 60
    hours, mins, secs = ['0' + i if len(i) == 1 else i for i in [str(hours), str(mins), str(secs)]]
    return f'{hours}:{mins}:{secs}'


def clear_widget(widget):
    for i in widget.children():
        if i.children():
            clear_widget(i)
        check_func = getattr(i, "destroy", None)
        if callable(check_func):
            i.destroy()
        i.deleteLater()


def clear_layout(layout, delete=False):
    for i in reversed(range(layout.count())):
        temp = layout.itemAt(i).widget()
        layout.removeWidget(temp)
        if delete:
            temp.deleteLater()
        else:
            temp.setVisible(False)


def resize_font(el, font=None, text=None):
    # font setting
    if font is None:
        font = el.font()
        real_bound = el.contentsRect()
        text = el.text()
    else:
        real_bound = el
    last_inc = {
        'val': font.pointSize() / 2,
        'dir': 'none'
    }
    step = 0
    while True:
        if step > 100:
            break
        font_size = font.pointSize()
        test_font = QFont(font)
        test_font.setPointSize(font.pointSize() + 1)
        test_bound = QFontMetrics(test_font).boundingRect(text)
        bound = QFontMetrics(font).boundingRect(text)
        if bound.width() > real_bound.width() or bound.height() > real_bound.height():
            if last_inc['dir'] == 'up' or last_inc['dir'] == 'tilt':
                font.setPointSize(font_size - last_inc['val'])
                last_inc['val'] /= 2
                last_inc['dir'] = 'tilt'
            else:
                font.setPointSize(font_size - font_size / 2)
                last_inc['val'] = abs(font.pointSize() - font_size)
                last_inc['dir'] = 'down'
        elif test_bound.width() < real_bound.width() and test_bound.height() < real_bound.height():
            if last_inc['dir'] == 'down' or last_inc['dir'] == 'tilt':
                font.setPointSize(font_size + last_inc['val'])
                last_inc['val'] /= 2
                last_inc['dir'] = 'tilt'
            else:
                font.setPointSize(font_size + font_size / 2)
                last_inc['val'] = abs(font.pointSize() - font_size)
                last_inc['dir'] = 'up'
        else:
            break
        step += 1
    return font, step
    