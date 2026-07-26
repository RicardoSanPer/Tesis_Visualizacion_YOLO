# Compilación de pyopenvdb
El siguiente documento detalla el proceso que se siguió para la compilación de OpenVDB para Python.

## Requisitos
- CMake
- Visual Studio
    - Componente "Desarrollo para el escritorio con C++"
    - Componente "Herramientas de compilación de C++ de MSVC v143-VS 2022 para x64/86 (más recientes)"
    - SDK de Windows 11
    - Herramientas de CMake en C++ para Windows
    - ATL de C++ para las herramientas de compilación v143 más recientes (x86 y x64)
- Python
- Git

## Instrucciones
Los siguientes comandos descargan `vcpkg` en el directorio raíz `C:\`. `vcpkg` es un administrador de paquetería para C/C++, e instala herramientas requeridas para compilar `openvdb`:
~~~
cd C:\
git clone https://github.com/microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
~~~

EL siguiente comando utiliza `vcpkg` para instalar y compilar varias dependencias requeridas para `openvdb`. El proceso tarda 15-20 minutos.

~~~
.\vcpkg install tbb blosc boost-iostreams boost-system boost-any boost-algorithm openexr imath zlib nanobind boost-interprocess boost-headers:x64-windows
~~~

Tarda 10-15 minutos.

El siguiente descarga el código fuente de OpenVDB en el directorio raíz y crea un directorio donde colocar los archivos a compilar.
~~~
cd C:\
git clone https://github.com/AcademySoftwareFoundation/openvdb.git
cd openvdb
mkdir build
cd build
~~~

El siguiente comando genera la configuración de CMake para compilar OpenVDB, ejecutandolo desde el directorio `build` creado en el paso anterior. Se debe cambiar el valor de `-DPython_EXECUTABLE` al directorio donde se encuentra el ejecutable de Python de la versión para la cual se quiere compilar, y `"Visual Studio 17 2022"` debe cambiarse por la versión correcta de Visual Studio si se utiliza una distinta.

~~~
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_PREFIX_PATH="C:/vcpkg/installed/x64-windows" -DOPENVDB_BUILD_CORE=ON -DOPENVDB_BUILD_PYTHON_MODULE=ON -DPython_EXECUTABLE="C:/path/a/instalacion/de/python/python.exe" -DUSE_BLOSC=ON -DUSE_TBB=ON
~~~

Las instalaciones de Python suelen encontrarse en `C:\Users\usuario\AppData\Local\Programs\Python\Python3xx\python.exe`. Se recomienda utilizar la instalación nativa de Python en el sistema para evitar problemas de dependencias.

Finalmente el siguiente comando compila OpenVDB para Python:
~~~
cmake --build . --config Release --target openvdb_python
~~~

La biblioteca se crea en `C:/openvdb/build/openvdb/openvdb/python/Release/openvdb.cp3XX-win_amd.pyd` (el nombre del archivo cambia dependiendo de la versión de Python para el que se compiló).

Finalmente se copian los archivos de los siguientes directios:

`C:\openvdb\build\openvdb\openvdb\python\Release`:
- openvdb.cp3xx-wind_amd64.pyd

`C:\openvdb\build\openvdb\openvdb\Release`:
- openvdb.dll

`C:\vcpkg\installed\x64-windows\bin`:
- tbb12.dll
- z.dll
- zstd.dll
- blosc.dll
- lz4.dll
- openvdb.dll

Al directorio `Lib/site-packages` del ambiente virtual.

## Verificación

La instalación se puede verificar ejecutando el interprete de Python e importando `openvdb` con:

~~~
import openvdb
~~~

