from PyQt5.QtGui import QIcon

from h3_toolkit.processing.provider import H3Provider

c = H3Provider(iconPath='path/to/icon.svg')

def test_id():
    result = c.id()
    assert  result == 'h3', 'Incorrect provider ID'

def test_name():
    result = c.name()
    assert result == 'H3', 'Incorrect provider name'

def test_svgIconPath():
    result = c.svgIconPath()
    assert result == 'path/to/icon.svg'

def test_icon():
    result = c.icon()
    assert isinstance(result, QIcon)