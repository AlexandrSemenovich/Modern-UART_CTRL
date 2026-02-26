# Launcher

Планируемый лаунчер выполняет:

1. Проверяет `%APPDATA%/OrbSterm`.
2. Распаковывает `build/resources/resources.zip` при первом запуске/обновлении.
3. Копирует конфиги в `%APPDATA%/OrbSterm/config` (если отсутствуют).
4. Запускает встроенный Python (`runtime/python.exe`) с `src/main.py`.

TODO: Реализовать на C++/C#.
