## This document contains the list of all possible command-line parameters for every sinner module

# Sinner: The main application
* `--max-memory`: the maximum amount of RAM (in GB) that will be allowed for use. Defaults to `4` for Mac and `16` for any other platforms.
**Note 1**: AI processing usually requires a significant amount of RAM. While processing, you will see the memory usage statistics, and the `MEM LIMIT REACHED` statistics indicate a lack of RAM.
**Note 2**: This parameter does not affect the amount of used video RAM if a GPU-accelerated `execution-provider` is used.
* `--gui`: run application in the graphic mode. Defaults to `false`.
* `--benchmark`: run a benchmark on a selected frame processor to determine the optimal value for the execution-threads parameter (see also [Benchmark module parameters](#benchmark-the-benchmarking-module)). Defaults to `false`.
* `--ini`: optional path to a custom configuration file, see the [Configuration file](../README.md#configuration-file) section.
* `--h`, `--help`: show the help summary.

# BatchProcessingCore:: The main handler for batch processing
* `--execution-threads`: configures the count of parallel simultaneous processing tasks. This value heavily depends on your hardware capabilities — how many computing cores it has, and what amount of memory it can use. Let's say, you have a CPU with 32 cores — so you can set `--execution-threads=32` and `--execution-provider=cpu` to use all its computing powers. In another case, a GPU with thousands of CUDA cores will probably be much faster in total, but one thread will also require a lot of those cores to work with. For that case, I recommend doing some experiments, or run the [benchmark](#benchmark-the-benchmarking-module). Defaults to 1.
* `--target-path`, `--target`: path to the target file or directory (depends on used frame processors set).
* `--output`, `--output-path`: path to the resulting file or directory (depends on used frame processors set and target).
* `--processors`, `--frame-processor`, `--processor`: the frame processor module or modules that you want to apply to your files. See the [Built-in frame processors](../README.md#built-in-frame-processors) documentation for the list of built-in modules and their possibilities.
* `--keep-frames`: keeps processed frames in the temp directory after finishing. Defaults to `false`.

# GUI: GUI module
* `--frames-widget`, `--show-frames-widget`: show processed frames widget. It shows all stages of selected frame processing.
* `--frames-widget-width`, `--fw-width`: processed widget maximum width, -1 to set as 10% of original image size.
* `--frames-widget-height`, `--fw-height`: processed widget maximum height, -1 to set as 10% of original image size.

# WebCam: The virtual camera module
**Note**: You may need to install OBS drivers to create virtual camera device.
* `--auto-restart`, `--restart`: try to restart input camera on error (may help with buggy drivers/hardware).
* `--device`, `--output-device`: the output device name (e.g. virtual camera device to use). Ignore parameter to use the first available device or pass "no" to skip output at all.
* `--fps`: The output virtual device fps.
* `--width`: The output virtual device resolution width.
* `--height`: The output virtual device resolution height.
* `--input`, `--input-device`: Input camera index (ignore, if you have only one camera device). Pass a path to an image/video file to use it as the input.
* `--preview`: Show virtual camera preview in a separate window.
* `--print-fps`: Print frame rate every second.
* `--processors`, `--processor`, `--frame-processor`: the set of frame processors to handle the camera input. See the [Built-in frame processors](../README.md#built-in-frame-processors) documentation for the list of built-in modules and their possibilities.

# Benchmark: The benchmarking module
* `--source-path`, `--source`: the image file containing a face for `FaceSwapper` benchmarking.
* `--target-path`, `--target`: the target file (image or video) or the images containing directory.
* `--output`, `--output-path`: the output file or a directory.
* `--many-faces`: enable every face processing in the target. Defaults to `true`.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.
* `--frame-processor`: the frame processor for benchmarking. Defaults to FaceSwapper.

# FaceSwapper: This module swaps faces on images
* `--execution-provider`: this parameter specifies what kind of driver should be used to produce AI magic, and it depends on what your hardware and software capabilities are. The `cpu` provider should fit as a basic choice, but any GPU-accelerated option is worth trying. Defaults to cpu.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.
* `--source-path`, `--source`: the image file containing a face, which will be used for deepfake magic.
* `--target-path`, `--target`: an image, a video file, or a directory with image files for processing.
* `--output`, `--output-path`: a path (either a file or a directory) to save the processing result. If not provided, the resulting file will be saved near the target with an automatically generated filename.
* `--many-faces`: if set to `true`, every frame processor in the processing chain will apply its magic to every face on every frame of the `target`. If set to `false`, only one face (the first one found, no heavy logic here) will be processed. Defaults to `false`.
* `--target-gender`, `--gender`: this parameter allows for more precise control over the face swapping process, limiting swaps to faces of a specific gender or matching the gender of the source face. If the gender of a face cannot be determined, that face will be skipped during processing (except when `--target-gender=B`). Possible values:
  - `M`: Swap only male faces
  - `F`: Swap only female faces
  - `B`: Swap faces of both genders (default)
  - `I`: Swap faces of the same gender as the input face
<br/>Note: sex recognition can be inaccurate. 

* `--less-output`: if set to `true` all console outputs from the 3rd party runtime models will be silenced. Those outputs usually contain parameters of self-configuration and other stuff, that you can skip without pain. Defaults to `true`.

# FaceEnhancer: This module enhances faces on images
* `--execution-provider`: this parameter specifies what kind of driver should be used to produce AI magic, and it depends on what your hardware and software capabilities are. The `cpu` provider should fit as a basic choice, but any GPU-accelerated option is worth trying. Defaults to cpu.
* `--target-path`, `--target`: an image, a video file, or a directory with image files for processing.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.
* `--output`, `--output-path`: a path (either a file or a directory) to save the processing result. If not provided, the resulting file will be saved near the target with an automatically generated filename.
* `--less-output`: if set to `true` all console outputs from the 3rd party runtime models will be silenced. Those outputs usually contain parameters of self-configuration and other stuff, that you can skip without pain. Defaults to `true`.
* `--upscale`: scales output frames to certain float value. Example: `--upscale=0.5` will halve frame in both size and `--upscale=2` will zoom it twice.
**Note**: You can combine this parameter with `FrameResizer` scaling possibilities. As example:
```cmd
python sin.py --target="d:\videos\not_a_porn.mp4" --frame-processor FrameResizer FaceEnhancer --output="d:\results\result.mp4" --scale=0.5 --upscale=2
```
Thus, all frames will be halved before enhancing, and restored to original size with FaceEnhancer with its magic. The profit is that the processing of smaller frames can be faster. Defaults to 1.

# FrameExtractor: This module extracts frames from video file as set of png images
* `--target-path`, `--target`: a path to the target video file.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.

# FrameResizer: This module changes images resolution
* `--target-path`, `--target`: an image, a video file, or a directory with image files for processing.
* `--temp-dir`: a way to provide a directory, where processed frames will be saved. Defaults to the `temp` subdirectory in the application directory.
* `--output`, `--output-path`: a path (either a file or a directory) to save the processing result. If not provided, the resulting file will be saved near the target with an automatically generated filename.
* `--scale`: scales output frames to certain float value. Example: `--scale=0.5` will halve frame in both size and `--scale=2` will zoom it twice. Defaults to 1.
* `--height`: set output frames height to this integer value, the width also will be scaled proportionally.
* `--width`: set output frames width to this integer value, the height also will be scaled proportionally.
* `--height-max`: set output frames height to this integer value, but only if current frame height is greater. The width also will be scaled proportionally.
* `--width-max`: set output frames width to this integer value, but only if current frame width is greater. The height also will be scaled proportionally.
* `--height-min`: set output frames height to this integer value, but only if current frame height is smaller. The width also will be scaled proportionally.
* `--width-min`: set output frames width to this integer value, but only if current frame width is smaller. The width also will be scaled proportionally.
**Note**: The size keys priority is: all `height` keys will be used in the first place; if they skipped, then all `width` keys will be used; and if no `height` or `width` keys are provided, then `scale` key is used.

# VideoHandler: The video processing module, based on ffmpeg
* `--output-fps`: the parameter to set the frames per second (FPS) in the resulting video. If not provided, the resulting video's FPS will be the same as the `target`'s video (or 30, if an image directory is used as the `target`).
* `--keep-audio`: keeps the original audio in the resulting video. Defaults to `false`.