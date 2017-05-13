# -*- mode: python -*-

# Files to include in collection
added_files1 = [
  ('README.md', '.' ),
  ('LICENSE.txt', '.' )
]

a = Analysis(
  ['misnersplunktool.py'],
  hookspath=None,
  datas=added_files1,
  excludes=[
    'FixTk',
	'tcl',
	'tk',
	'_tkinter',
	'tkinter',
	'Tkinter',
	'certifi'
  ]
)

# Files to exclude from collection
a.binaries = a.binaries - TOC([
 ('sqlite3.dll', None, None),
 ('_sqlite3', None, None),
 ('mfc90.dll', None, None),
 ('mfc90u.dll', None, None),
 ('mfcm90.dll', None, None),
 ('mfcm90u.dll', None, None),
 ('msvcr90.dll', None, None),
 ('msvcm90.dll', None, None),
 ('tcl85.dll', None, None),
 ('tk85.dll', None, None),
 ('Tkinter', None, None),
 ('tk', None, None),
 ('_tkinter', None, None)
])

pyz = PYZ(
  a.pure
)

exe = EXE(
  pyz,
  a.scripts,
  exclude_binaries=True,
  name='misnersplunktool',
  debug=False,
  strip=False,
  upx=True,
  console=False,
  icon='favorites.ico'
)

coll = COLLECT(
  exe,
  a.binaries,
  a.zipfiles,
  a.datas,
  strip=False,
  upx=True,
  name='Misner Splunk Tool'
)
