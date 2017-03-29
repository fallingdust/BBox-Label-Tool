from distutils.core import setup
import py2exe

setup(windows=[{'script': "main.py"}],
      zipfile=None,
      options={'py2exe': {'bundle_files': 1, 'compressed': True, "dll_excludes": ["tcl85.dll", "tk85.dll"]}}
      )