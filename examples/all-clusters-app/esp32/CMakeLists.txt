#
#    Copyright (c) 2021 Project CHIP Authors
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# The following lines of boilerplate have to be in your project's
# CMakeLists in this exact order for cmake to work correctly
cmake_minimum_required(VERSION 3.5)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_LIST_DIR}/third_party/connectedhomeip/config/esp32/components"
    "${CMAKE_CURRENT_LIST_DIR}/../../common/QRCode"
)
if(${IDF_TARGET} STREQUAL "esp32")
set(EXTRA_COMPONENT_DIRS
    ${EXTRA_COMPONENT_DIRS}
    "${CMAKE_CURRENT_LIST_DIR}/../../common/m5stack-tft/repo/components/tft"
    "${CMAKE_CURRENT_LIST_DIR}/../../common/m5stack-tft/repo/components/spidriver"
    "${CMAKE_CURRENT_LIST_DIR}/../../common/screen-framework"
)
endif()

project(chip-all-clusters-app)
idf_build_set_property(CXX_COMPILE_OPTIONS "-std=gnu++17;-Os;-DLWIP_IPV6_SCOPES=0;-DCHIP_HAVE_CONFIG_H" APPEND)
idf_build_set_property(C_COMPILE_OPTIONS "-Os;-DLWIP_IPV6_SCOPES=0" APPEND)

idf_build_get_property(build_dir BUILD_DIR)
idf_build_get_property(project_path PROJECT_DIR)
idf_build_get_property(sdkconfig SDKCONFIG)
idf_build_get_property(idf_path IDF_PATH)

add_custom_command(OUTPUT "${build_dir}/firmware_utils.py"
    COMMAND ${CMAKE_COMMAND} ARGS -E copy "${project_path}/third_party/connectedhomeip/scripts/flashing/firmware_utils.py" "${build_dir}/"
    WORKING_DIRECTORY ${build_dir}
    VERBATIM)

add_custom_command(OUTPUT "${build_dir}/esp32_firmware_utils.py"
    COMMAND ${CMAKE_COMMAND} ARGS -E copy "${project_path}/third_party/connectedhomeip/scripts/flashing/esp32_firmware_utils.py" "${build_dir}/"
    WORKING_DIRECTORY ${build_dir}
    VERBATIM)

add_custom_command(OUTPUT "${build_dir}/${CMAKE_PROJECT_NAME}.flash.py"
    COMMAND ${python}
            "${project_path}/../../../scripts/flashing/gen_flashing_script.py" esp32
            --output "${build_dir}/${CMAKE_PROJECT_NAME}.flash.py"
            --port "$ENV{ESPPORT}"
            --baud "$ENV{ESPBAUD}"
            --before ${CONFIG_ESPTOOLPY_BEFORE}
            --after ${CONFIG_ESPTOOLPY_AFTER}
            --application "${CMAKE_PROJECT_NAME}.bin"
            --bootloader "bootloader/bootloader.bin"
            --partition "partition_table/partition-table.bin"
            --use-partition-file "${build_dir}/partition_table/partition-table.bin"
            --use-parttool ${idf_path}/components/partition_table/parttool.py
            --use-sdkconfig ${project_path}/sdkconfig
    WORKING_DIRECTORY ${build_dir}
    COMMENT "To flash ${build_dir}/${CMAKE_PROJECT_NAME}.bin run ./build/${CMAKE_PROJECT_NAME}.flash.py"
    VERBATIM)

add_custom_target(flashing_script DEPENDS "${build_dir}/${CMAKE_PROJECT_NAME}.bin" "${build_dir}/${CMAKE_PROJECT_NAME}.flash.py" "${build_dir}/esp32_firmware_utils.py" "${build_dir}/firmware_utils.py")

if (CONFIG_ENABLE_PW_RPC)
get_filename_component(CHIP_ROOT ./third_party/connectedhomeip REALPATH)
include(third_party/connectedhomeip/third_party/pigweed/repo/pw_build/pigweed.cmake)
pw_set_backend(pw_log pw_log_basic)
pw_set_backend(pw_assert pw_assert_log)
pw_set_backend(pw_sys_io pw_sys_io.esp32)
pw_set_backend(pw_trace pw_trace_tokenized)

add_subdirectory(third_party/connectedhomeip/third_party/pigweed/repo)
add_subdirectory(third_party/connectedhomeip/third_party/nanopb/repo)
add_subdirectory(third_party/connectedhomeip/examples/platform/esp32/pw_sys_io)

get_target_property(_target_cxx_flags pw_build.cpp17 INTERFACE_COMPILE_OPTIONS)
list(REMOVE_ITEM _target_cxx_flags $<$<COMPILE_LANGUAGE:CXX>:-std=c++17>)
list(APPEND _target_cxx_flags $<$<COMPILE_LANGUAGE:CXX>:-std=gnu++17>)
set_target_properties(pw_build.cpp17 PROPERTIES INTERFACE_COMPILE_OPTIONS "${_target_cxx_flags}")
endif(CONFIG_ENABLE_PW_RPC)
