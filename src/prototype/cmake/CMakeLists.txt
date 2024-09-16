cmake_minimum_required(VERSION 3.10)

project(my_project)

# Download and build an external dependency from the custom registry
include(ExternalProject)

ExternalProject_Add(
    my_package
    PREFIX ${CMAKE_BINARY_DIR}/my_package
    URL http://localhost:5000/my-package/-/my-package-1.0.0.tar.gz
    BUILD_IN_SOURCE 1
    CONFIGURE_COMMAND cmake .
    BUILD_COMMAND cmake --build .
    INSTALL_COMMAND ""
)

# Define the target for your main project
add_executable(${PROJECT_NAME} src/main.cpp)

# Link the external project library to your target (adjust path as necessary)
add_dependencies(${PROJECT_NAME} my_package)
target_link_libraries(${PROJECT_NAME} ${CMAKE_BINARY_DIR}/my_package-prefix/src/my_package/libmylibrary.a)