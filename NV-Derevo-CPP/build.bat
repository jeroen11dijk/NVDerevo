cd NV-Derevo

del build\\Debug\\my_bot.exe
del build\\bin\\Debug\\rlutilities.dll

cmake -DTARGET_LANGUAGE=cpp -A x64 -B build
cmake --build build --config Release

del release\\my_bot.exe
del release\\rlutilities.dll

copy build\\Release\\my_bot.exe release
copy build\\bin\\Release\\rlutilities.dll release