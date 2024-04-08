# Compilation

To compile python files you need to install PyInstaller

```shell
python -m pip install pyinstaller
```

## Windows

````shell
pyinstaller -F --distpath "compiled\Windows\dist" --workpath "compiled\Windows\build" --specpath "compiled\Windows" --clean [filename]
````

## Linux with Gnome

````shell
pyinstaller -F --distpath "compiled/Linux/dist" --workpath "compiled/Linux/build" --specpath "compiled/Linux" --clean [filename]
````
