[![Build Status](https://github.com/pozitronik/roop/actions/workflows/ci.yml/badge.svg)](https://github.com/pozitronik/roop/actions)

# sinner: sinner is non exactly roop

Deepfakes and more.

# What is it?

This is the rework of the [s0md3v/roop](https://github.com/s0md3v/roop/) that I'm working on for entertainment and educational purposes. It doesn't aim to be popular; it's just a fork made the way I want it to be.
The tasks that I aim to accomplish here are:

- :white_check_mark: Rewriting the code using object-oriented programming (OOP).
- :white_check_mark: Providing a clear and user-friendly API for creating processing modules.
- :white_check_mark: Supporting different input and output data types through frame handlers.
- :white_check_mark: Implementing strict typing and static analysis for improved code quality.
- :white_check_mark: Enabling in-memory processing without the need for temporary frames.
- :white_check_mark: Allowing the ability to resume processing after a stop.
- :white_check_mark: Implementing a continuous frames processing chain.
- :white_check_mark: Implementing memory control code.
- :white_check_mark: Providing code coverage through comprehensive tests.

## How do I install it?

The basic installation instructions for now are the same as those in the [s0md3v/roop](https://github.com/s0md3v/roop#how-do-i-install-it), check them out.
In short, you need to install python 3.9 or a later version, VC runtimes, and desired Execution Provider kit (depending on your hardware and OS).

## How do I use it?

Go to application folder and run `python run.py` with desired set of command-line parameters (or just pick one of the [example](#command-line-usage-examples) and make changes to suit your need).

Here is the list of all possible command-line parameters. 
* `--source`: the image file containing a face, which will be used for deepfake magic.
* `--target`: an image, a video file, or a directory with PNG images for processing.
* `--output`: a path (either a file or a directory) to save the processing result. If not provided, the resulting file will be saved near the target with an automatically generated filename.
* `--frame-processor`: the frame processor module or modules that you want to apply to your files. See the [built-in frame processors](#built-in-frame-processors) section for the list of built-in modules and their possibilities.
* `--frame-handler`: a module to handle the `target`. In the most cases, you should omit that parameter (sinner will figure it out itself).
* `--fps`: the parameter to set the frames per second (FPS) in the resulting video. If not provided, the resulting video's FPS will be the same as the `target`'s video (or 30, if an image directory is used as the `target`).
* `--keep-audio`: defaults to `true`. Keeps the original audio in the resulting video.
* `--keep-frames`: defaults to `false`. Keeps processed frames in the `temp-dir` after finishing.
* `--many-faces`: defaults to `false`. If set to true, every frame processor in the processing chain will apply its magic to every face on every frame of the `target`. If set to `false`, only one face (the first one found, no heavy logic here) will be processed.
* `--max-memory`: defaults to `4` for Mac and `16` for any other platforms. The maximum amount of gigabytes of RAM that will be allowed for sinner use.
**Note 1**: AI processing usually requires a significant amount of RAM. While processing, you will see the memory usage statistics, and the `MEM LIMIT REACHED` statistics indicate a lack of RAM.
**Note 2**: This parameter does not affect the amount of used video RAM if a GPU-accelerated `execution-provider` is used.
* `--execution-provider`: defaults to `cpu`. This parameter specifies what kind of driver should be used to produce AI magic, and it depends on what your hardware and software capabilities. The `cpu` provider should fit as a basic choice, but any GPU-accelerated option is worth trying.
* `--execution-threads`: defaults to `1`. Configures the count of parallel simultaneous processing tasks. This value heavily depends on your hardware capabilities — how many computing cores it has, and what amount of memory it can use. Let's say, you have a CPU with 32 cores — so you can set `--execution-threads=32` and `--execution-provider=cpu` to use all its computing powers. In another case, a GPU with thousands of CUDA cores, will probably be much faster in total, but one thread will also require a lot of those cores to work with. For that case, I recommend doing some experiments, or waiting until the benchmark mode is implemented in sinner.
* `--extract-frames`: defaults to `false`. If set to true, all frames from the `target` will be extracted to a temporary folder as a sequence of PNG files right before processing. If set to false, every frame will be extracted to a memory only by a processor module's request. The first way requires some disk space for temporary frames, the second way might be a little slower in some cases.
* `--temp-dir`: defaults to the `temp` subdirectory in the application directory. A way to provide a directory, where processed (and, in the case of `--in-memory=false`, extracted too) frames will be saved.
* `--benchmark`: runs a benchmark on a selected `frame-processor` to determine the optimal value for the execution-threads parameter. Additionally, you can specify the `--execution-provider` parameter to choose a specific execution provider (if not provided, all available providers will be tried in sequence). Furthermore, you have the option to specify the `--source` and `--target` parameters to use custom files during the benchmark (if not provided, default test files will be used).
* `--gui`: starts in GUI mode (experimental).

**FrameResizer:**
* `--scale`: Scales output frames to certain float value. Example: `--scale=0.5` will halve frame in both size and `--scale=2` will zoom it twice. 
* `--height`: Set output frames height to this integer value, the width also will be scaled proportional.
* `--width`: Set output frames width to this integer value, the height also will be scaled proportional.
* `--height-max`: Set output frames height to this integer value, but only if current frame height is greater. The width also will be scaled proportional.
* `--width-max`: Set output frames width to this integer value, but only if current frame width is greater. The width also will be scaled proportional.
* `--height-max`: Set output frames height to this integer value, but only if current frame height is smaller. The width also will be scaled proportional.
* `--width-max`: Set output frames width to this integer value, but only if current frame width is smaller. The width also will be scaled proportional.
**Note**: The size keys priority is: all `height` keys will be used in the first place; if they skipped, then all `width` keys will be used; and if no `height` or `width` keys are provided, then `scale` key is used.

**FaceEnhancer:**
* `--upscale`: Scales output frames to certain float value. Example: `--scale=0.5` will halve frame in both size and `--scale=2` will zoom it twice.
**Note**: You can combine this parameter with `FrameResizer` scaling possibilities. As example:
```cmd
python run.py --target="d:\videos\not_a_porn.mp4" --frame-processor FrameResizer FaceEnhancer --output="d:\results\result.mp4" --scale=0.5 --upscale=2
```
Thus, all frames will be halved before enhancing, and restored to original size with FaceEnhancer with its magic. The profit is that the processing of smaller frames can be faster. 

## Built-in frame processors

There are modules named frame processors, and each processor can perform its own type of magic. You need to choose which frame processor (or processors)
you want to use, and provide them with some sources to work on. Here is the list of built-in frame processors: 
- `FaceSwapper`: performs face-swapping deepfake magic. It substitutes a face from the `source` to a face (or faces) in the `target`. The processor is based on the [insightface project example](https://github.com/deepinsight/insightface/blob/master/examples/in_swapper/inswapper_main.py) code.
![FaceSwapper demo](/demos/swapper-demo.gif)
- `FaceEnhancer`: performs face restoration and enhances the quality of the `target`. The processor is based on the libraries of the [ARC Lab GFPGAN project](https://github.com/TencentARC/GFPGAN).
![FaceEnhancer demo](/demos/enhancer-demo.jpg)
- `FrameResizer`: resizes frames to certain size.
- `DummyProcessor`: literally does nothing; it is just a test tool.

## Command line usage examples

```cmd
python run.py --source="d:\pictures\cool_photo.jpg" --target="d:\pictures\other_cool_photo.jpg" --frame-processor=FaceSwapper
```
Swap one face on the `d:\pictures\other_cool_photo.jpg` picture to face from the `d:\pictures\cool_photo.jpg` picture and save resulting image to `d:\pictures\cool_photo_other_cool_photo.png` (autogenerated name).
```cmd
python run.py --source="d:\pictures\cool_photo.jpg" --target="d:\videos\not_a_porn.mp4" --frame-processor FaceSwapper FaceEnhancer --output="d:\results\result.mp4" --many-faces --execution-provider=cuda
```
Swap all faces on the `d:\videos\not_a_porn.mp4` video file to the face from `d:\pictures\cool_photo.jpg` and enhance all faces quality, both processing will be made using the `cuda` provider, and result will be saved to the `d:\results\result.mp4`.
```cmd
python run.py --source="d:\pictures\any_picture.jpg" --target="d:\pictures\pngs_dir" --output="d:\pictures\pngs_dir\enhanced" --frame-processor=FaceEnhancer --many-faces --max-memory=24 --execution-provider=cuda --execution-threads=8
```
Enhance all faces in every PNG file in the `d:\pictures\pngs_dir` directory using the `cuda` provider and 8 simultaneous execution threads, with limit of 24 Gb RAM, and save every enhanced image to the `d:\pictures\pngs_dir\enhanced` directory.<br/>
**Note 1**: only PNG images are supported at the moment.<br/>
**Note 2**: even if the selected frame processor does not require a `source`, you should provide one at this time.

## FAQ

:question: What are the differences between sinner and roop?<br/>
:exclamation: As said before, sinner has started as a fork of roop. They share similar ideas, but they differ in the ways how those ideas should be implemented.
sinner uses the same ML libraries to perform its magic, but handles them in its own way. From a developer's perspective, it has a better architecture (OOP instead of functional approach),
 stricter types handling and more comprehensive tests. From the point of view of a user, sinner offers additional features that Roop currently lacks.

:question: Is there a NSWF filter?<br/>
:exclamation: Nope. I don't care if you will do nasty things with sinner, it's your responsibility. And sinner is just a neutral tool, like a hammer or a knife, it is the responsibility of the user to decide how they want to use it.

:question: Is there a graphic interface?<br/>
:exclamation:Yes, but it still in development. You can start the program with `--gui` parameter to enable GUI.

:question: Can I use several execution providers simultaneously?<br/>
:exclamation: You can try. Seriously, you can set `--execution-provider cuda cpu`, and look, what will happen. May be it will work faster, may be it won't work at all. It is a large space for experiments.


## Credits

- [s0md3v](https://github.com/s0md3v/): the original author of roop
- [henryruhs](https://github.com/henryruhs): the significant contributor to roop
- [ffmpeg](https://ffmpeg.org/): for making video related operations easy
- [deepinsight](https://github.com/deepinsight): for their [insightface](https://github.com/deepinsight/insightface) project which provided a well-made library and models.
- [ARC Lab, Tencent PCG](https://github.com/TencentARC): for their [GFPGAN](https://github.com/TencentARC/GFPGAN) project which provided a face restoration library and models.
- and all developers behind libraries used in this project.

## License

GNU GPL 3.0