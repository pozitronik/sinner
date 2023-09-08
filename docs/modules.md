## This document contains the list of all possible command-line parameters for every sinner module

# Sinner: The main application
* `--max-memory`: the maximum amount of RAM (in GB) that will be allowed for use. Defaults to `4` for Mac and `16` for any other platforms.
**Note 1**: AI processing usually requires a significant amount of RAM. While processing, you will see the memory usage statistics, and the `MEM LIMIT REACHED` statistics indicate a lack of RAM.
**Note 2**: This parameter does not affect the amount of used video RAM if a GPU-accelerated `execution-provider` is used.
* `--gui`: run application in a graphic mode. Defaults to `false`.
* `--benchmark`: run a benchmark on a selected frame processor to determine the optimal value for the execution-threads parameter (see also [Benchmark module parameters](#benchmark-the-benchmarking-module)). Defaults to `false`.
* `--ini`: optional path to a custom configuration file, see the [Configuration file](../README.md#configuration-file) section.
* `--h`, `--help`: show the help summary.

# Core: The main handler for the processing modules
* `--target-path`, `--target`: path to the target file or directory (depends on used frame processors set).
* `--output`, `--output-path`: path to the resulting file or directory (depends on used frame processors set and target).
* `--processors`, `--frame-processor`, `--processor`: the frame processor module or modules that you want to apply to your files. See the [Built-in frame processors](../README.md#built-in-frame-processors) documentation for the list of built-in modules and their possibilities.
* `--keep-frames`: keeps processed frames in the temp directory after finishing. Defaults to `false`.
# Status: The status messaging module
* `--logfile`, `--log`: optional path to a logfile where all status messages will be logged (if ignored, no logs will be stored).
* `--enable-emoji`: enable modules emoji prefixes in their message statuses, if supported in the current console.
* 
# Preview: GUI module
* `--preview-height-max`, `--preview-max-height`: maximum preview window height.
* `--preview-max-width`, `--preview-width-max`: maximum preview window width.

# Benchmark: The benchmarking module
* `--source-path`, `--source`: the image file containing a face for `FaceSwapper` benchmarking.
* `--target-path`, `--target`: the target file (image or video) or the images containing directory.
* `--output`, `--output-path`: the output file or a directory.
* `--many-faces`: enable every face processing in the target. Defaults to `true`.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.
* `--frame-processor`: the frame processor for benchmarking. Defaults to FaceSwapper.

# FaceSwapper: This module swaps faces on images
* `--execution-provider`: this parameter specifies what kind of driver should be used to produce AI magic, and it depends on what your hardware and software capabilities. The `cpu` provider should fit as a basic choice, but any GPU-accelerated option is worth trying. Defaults to cpu.
* `--execution-threads`: configures the count of parallel simultaneous processing tasks. This value heavily depends on your hardware capabilities — how many computing cores it has, and what amount of memory it can use. Let's say, you have a CPU with 32 cores — so you can set `--execution-threads=32` and `--execution-provider=cpu` to use all its computing powers. In another case, a GPU with thousands of CUDA cores, will probably be much faster in total, but one thread will also require a lot of those cores to work with. For that case, I recommend doing some experiments, or run the [benchmark](#benchmark-the-benchmarking-module). Defaults to 1.
* `--target-path`, `--target`: an image, a video file, or a directory with image files for processing.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.
* `--source-path`, `--source`: the image file containing a face, which will be used for deepfake magic.
* `--target-path`, `--target`: an image, a video file, or a directory with image files for processing.
* `--output`, `--output-path`: a path (either a file or a directory) to save the processing result. If not provided, the resulting file will be saved near the target with an automatically generated filename.
* `--many-faces`: if set to `true`, every frame processor in the processing chain will apply its magic to every face on every frame of the `target`. If set to `false`, only one face (the first one found, no heavy logic here) will be processed. Defaults to `false`.
* `--less-output`: if set to `true` all console outputs from the 3rd party runtime models will be silenced. Those outputs usually contains parameters of self-configuration and other stuff, that you can skip without pain. Defaults to `true`.

# FaceEnhancer: This module enhances faces on images
* `--execution-provider`: this parameter specifies what kind of driver should be used to produce AI magic, and it depends on what your hardware and software capabilities. The `cpu` provider should fit as a basic choice, but any GPU-accelerated option is worth trying. Defaults to cpu.
* `--execution-threads`: configures the count of parallel simultaneous processing tasks. This value heavily depends on your hardware capabilities — how many computing cores it has, and what amount of memory it can use. Let's say, you have a CPU with 32 cores — so you can set `--execution-threads=32` and `--execution-provider=cpu` to use all its computing powers. In another case, a GPU with thousands of CUDA cores, will probably be much faster in total, but one thread will also require a lot of those cores to work with. For that case, I recommend doing some experiments, or run the [benchmark](#benchmark-the-benchmarking-module). Defaults to 1.
* `--target-path`, `--target`: an image, a video file, or a directory with image files for processing.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.
* `--output`, `--output-path`: a path (either a file or a directory) to save the processing result. If not provided, the resulting file will be saved near the target with an automatically generated filename.
* `--less-output`: if set to `true` all console outputs from the 3rd party runtime models will be silenced. Those outputs usually contains parameters of self-configuration and other stuff, that you can skip without pain. Defaults to `true`.
* `--upscale`: scales output frames to certain float value. Example: `--scale=0.5` will halve frame in both size and `--scale=2` will zoom it twice.
**Note**: You can combine this parameter with `FrameResizer` scaling possibilities. As example:
```cmd
python sin.py --target="d:\videos\not_a_porn.mp4" --frame-processor FrameResizer FaceEnhancer --output="d:\results\result.mp4" --scale=0.5 --upscale=2
```
Thus, all frames will be halved before enhancing, and restored to original size with FaceEnhancer with its magic. The profit is that the processing of smaller frames can be faster. Defaults to 1.

# FrameExtractor: This module extracts frames from video file as set of png images
* `--target-path`, `--target`: Select the target video file.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.

# FrameResizer: This module changes images resolution
* `--target-path`, `--target`: an image, a video file, or a directory with image files for processing.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.
* `--output`, `--output-path`: a path (either a file or a directory) to save the processing result. If not provided, the resulting file will be saved near the target with an automatically generated filename.
* `--scale`: scales output frames to certain float value. Example: `--scale=0.5` will halve frame in both size and `--scale=2` will zoom it twice. Defaults to 1.
* `--height`: set output frames height to this integer value, the width also will be scaled proportionally .
* `--width`: set output frames width to this integer value, the height also will be scaled proportionally .
* `--height-max`: set output frames height to this integer value, but only if current frame height is greater. The width also will be scaled proportionally.
* `--width-max`: set output frames width to this integer value, but only if current frame width is greater. The width also will be scaled proportionally.
* `--height-min`: set output frames height to this integer value, but only if current frame height is smaller. The width also will be scaled proportionally.
* `--width-min`: set output frames width to this integer value, but only if current frame width is smaller. The width also will be scaled proportionally.
**Note**: The size keys priority is: all `height` keys will be used in the first place; if they skipped, then all `width` keys will be used; and if no `height` or `width` keys are provided, then `scale` key is used.

# VideoHandler: The video processing module, based on ffmpeg
* `--output-fps`: the parameter to set the frames per second (FPS) in the resulting video. If not provided, the resulting video's FPS will be the same as the `target`'s video (or 30, if an image directory is used as the `target`).
* `--keep-audio`: keeps the original audio in the resulting video. Defaults to `false`.