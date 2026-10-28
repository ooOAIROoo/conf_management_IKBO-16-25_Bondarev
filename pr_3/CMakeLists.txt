cmake_minimum_required(VERSION 3.16)

project(emu_vfs
    VERSION 0.2.0
    DESCRIPTION "Эмулятор командной строки UNIX-подобной ОС с виртуальной файловой системой"
    LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Каталог, в котором лежит бинарник: удобно запускать демонстрационные скрипты
# из корня проекта, не копируя данные VFS.
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Тип сборки" FORCE)
endif()

if(MSVC)
    add_compile_options(/W4 /utf-8 /permissive-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

add_executable(emu
    src/main.cpp
    src/config.cpp
    src/lexer.cpp
    src/shell.cpp)

target_include_directories(emu PRIVATE include)

if(WIN32)
    # CommandLineToArgvW / WideCharToMultiByte нужны, чтобы корректно принимать
    # UTF-8 пути к VFS и скриптам в командной строке Windows.
    target_link_libraries(emu PRIVATE shell32)
endif()

install(TARGETS emu RUNTIME DESTINATION bin)
