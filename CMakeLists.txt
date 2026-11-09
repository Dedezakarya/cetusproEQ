cmake_minimum_required(VERSION 3.22)
project(cetusproEQ VERSION 0.1.0 LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if (DEFINED JUCE_PATH)
    add_subdirectory("${JUCE_PATH}" JUCE)
else()
    include(FetchContent)
    FetchContent_Declare(juce GIT_REPOSITORY https://github.com/juce-framework/JUCE.git GIT_TAG 8.0.10 GIT_SHALLOW TRUE)
    FetchContent_MakeAvailable(juce)
endif()
set(CETUS_FORMATS VST3 Standalone)
if(APPLE)
    list(APPEND CETUS_FORMATS AU)
endif()
juce_add_plugin(cetusproEQ
    COMPANY_NAME "Cetus Production"
    BUNDLE_ID "com.cetusproduction.cetusproeq"
    PLUGIN_MANUFACTURER_CODE CtPr
    PLUGIN_CODE CpEq
    PRODUCT_NAME "cetusproEQ"
    PLUGIN_NAME "cetusproEQ"
    FORMATS ${CETUS_FORMATS}
    VST3_CATEGORIES Fx EQ Dynamics
    AU_MAIN_TYPE kAudioUnitType_Effect
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE)
target_sources(cetusproEQ PRIVATE Source/PluginProcessor.cpp Source/PluginProcessor.h Source/PluginEditor.cpp Source/PluginEditor.h Source/CetusLink.h)
target_compile_definitions(cetusproEQ PUBLIC JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_VST3_CAN_REPLACE_VST2=0)
target_link_libraries(cetusproEQ PRIVATE juce::juce_audio_utils juce::juce_dsp PUBLIC juce::juce_recommended_config_flags juce::juce_recommended_lto_flags juce::juce_recommended_warning_flags)
juce_generate_juce_header(cetusproEQ)
