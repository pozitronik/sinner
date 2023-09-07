[![Build Status](https://github.com/pozitronik/sinner/actions/workflows/ci.yml/badge.svg)](https://github.com/pozitronik/sinner/actions)

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
In short, you need to install python 3.10 or a later version, VC runtimes (on windows), and desired Execution Provider kit (depending on your hardware and OS).
Then you need to install required python packages, and there are some differences in the process:

### I have PC with Windows/Linux and no CUDA GPU

Run `pip install -r requirements.txt`. It will install packages, just enough to run magic on CPU only.

### I have PC with Windows/Linux and GPU with CUDA support

Run `pip install -r requirements-pc-cuda.txt`. It will install packages with CUDA support. Do not forget: you also have to install CUDA drivers as well.

### I have x86 Mac 

Run `pip install -r requirements-mac-x86.txt`. It will use only CPU powers, but it should work.

### I have Apple Silicon Mac 

Run `pip install -r requirements-mac-arm64.txt`. There is no CUDA, obviously, but there's some hardware acceleration too.

Anyway, packages should be installed successfully. Otherwise, get a look to the command output, usually you may fix minor issues (like version requirements change) by yourself.

If nothing helps, feel free to create an issue with your problem, we will try to figure it out together.

## How do I use it?

Go to application folder and run `python sin.py` with desired set of command-line parameters (or just pick one of [examples](#command-line-usage-examples) and make changes to suit your need).

You can get the list of all available command-line parameters by running the program with `--h` or `--help` keys. Those commands will list all configurable modules and their supported parameters.

Some modules may have the same parameters. It is okay: those parameters (and its values) are shared. It is also okay, if parameters expected values are different between modules: usually, they will be harmonized in runtime. But if something goes wrong, you will get an explicit error message.

Also, you can read about modules parameters [here](/docs/modules.md)

## Built-in frame processors

There are modules named frame processors, and each processor can perform its own type of magic. You need to choose which frame processor (or processors)
you want to use, and provide them with some sources to work on. Here is the list of built-in frame processors: 
- `FaceSwapper`: performs face-swapping deepfake magic. It substitutes a face from the `source` to a face (or faces) in the `target`. The processor is based on the [insightface project example](https://github.com/deepinsight/insightface/blob/master/examples/in_swapper/inswapper_main.py) code.
![FaceSwapper demo](/demos/swapper-demo.gif)
- `FaceEnhancer`: performs face restoration and enhances the quality of the `target`. The processor is based on the libraries of the [ARC Lab GFPGAN project](https://github.com/TencentARC/GFPGAN).
![FaceEnhancer demo](/demos/enhancer-demo.jpg)
- `FrameExtractor`: use this processor in the processing chain when using video file as the target to force sinner extract frames to a temporary folder as a sequence of PNG files. If not used, every frame will be extracted into the memory by a processor module's request. The first way requires some disk space for temporary frames, the second way might be a little slower in some cases.
- `FrameResizer`: resizes frames to certain size.
- `DummyProcessor`: literally does nothing; it is just a test tool.

## Command line usage examples

```cmd
python sin.py --source="d:\pictures\cool_photo.jpg" --target="d:\pictures\other_cool_photo.jpg" --frame-processor=FaceSwapper
```
Swap one face on the `d:\pictures\other_cool_photo.jpg` picture to face from the `d:\pictures\cool_photo.jpg` picture and save resulting image to `d:\pictures\cool_photo_other_cool_photo.png` (autogenerated name).
```cmd
python sin.py --source="d:\pictures\cool_photo.jpg" --target="d:\videos\not_a_porn.mp4" --frame-processor FaceSwapper FaceEnhancer --output="d:\results\result.mp4" --many-faces --execution-provider=cuda
```
Swap all faces on the `d:\videos\not_a_porn.mp4` video file to the face from `d:\pictures\cool_photo.jpg` and enhance all faces quality, both processing will be made using the `cuda` provider, and result will be saved to the `d:\results\result.mp4`.
```cmd
python sin.py --source="d:\pictures\any_picture.jpg" --target="d:\pictures\pngs_dir" --output="d:\pictures\pngs_dir\enhanced" --frame-processor=FaceEnhancer --many-faces --max-memory=24 --execution-provider=cuda --execution-threads=8
```
Enhance all faces in every PNG file in the `d:\pictures\pngs_dir` directory using the `cuda` provider and 8 simultaneous execution threads, with limit of 24 Gb RAM, and save every enhanced image to the `d:\pictures\pngs_dir\enhanced` directory.<br/>

## Configuration file

You can store commonly used options in the configuration file, to make them apply on every run by default. Just edit `sinner.ini` file in the application directory and add desired parameters inside the `[sinner]` section as key-value pairs.

Example:
```ini
[sinner]
keep-frames=1
many-faces=1
execution-provider=gpu
execution-threads=2
```

It is also possible to configure modules separately this way. Just create/modify a config section with the module name, and all key-value pairs from this section will be applied only to that module.

Example:
```ini
[sinner]
execution-threads=2

[FaceSwapper]
execution-threads=4
```

In the example above FaceSwapper will run in four execution threads, when other modules will run in two threads (if they support this parameter).
Module configurations have the priority over global parameters (even if they passed directly from the command line).

Any parameter set from command line will override corresponding global (not module) parameter from the ini file.

You also can pass path to the custom configuration file as a command line parameter:
```cmd
python sin.py --ini="d:\path\custom.ini"
```

## How to handle output videos quality/encoding speed/etc?

In brief, sinner relies on the `ffmpeg` software almost every time video processing is required, and it's possible to utilize all the incredible powers of `ffmpeg`. Use the `--ffmpeg_resulting_parameters` key to control how `ffmpeg` will encode the output video: simply pass the usual `ffmpeg` parameters as the value for this key (remember not to forget enclosing the value string in commas). There are some examples:

* `--ffmpeg_resulting_parameters="-c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p"`: use software x264 encoder (`-c:v libx264`) with the medium quality (`-preset medium` and `-crf 20`) and `yuv420p` pixel format. This is the default parameter value.
* `--ffmpeg_resulting_parameters="-c:v h264_nvenc -preset slow -qp 20 -pix_fmt yuv420p"`: use nVidia GPU-accelerated x264 encoder (`-c:v h264_nvenc`) with the good encoding quality (`-preset slow` and `-qp 20`). This encoder is worth to use if it supported by your GPU.
* `--ffmpeg_resulting_parameters="-c:v hevc_nvenc -preset slow -qp 20 -pix_fmt yuv420p"`: the same as above, but with x265 encoding.
* `--ffmpeg_resulting_parameters="-c:v h264_amf -b:v 2M -pix_fmt yuv420p"`: the AMD hardware-accelerated x264 encoder (`-c:v h264_amf`) with 2mbps resulting video bitrate (-b:v 2M). This should be good for AMD GPUs.

And so on. As you can find, there are a lot of different presets and options for the every `ffmpeg` encoder, and you can rely on the [documentation](https://ffmpeg.org/ffmpeg-codecs.html) to achieve desired results. 

In case, when `ffmpeg` is not available in your system, sinner will gracefully degrade to CV2 library possibilities. In that case all video processing features should work, but in a very basic way: only with the software x264 encoder, which is slow and thriftless. 

## FAQ

:question: What are the differences between sinner and roop?<br/>
:exclamation: As said before, sinner has started as a fork of roop. They share similar ideas, but they differ in the ways how those ideas should be implemented.
sinner uses the same ML libraries to perform its magic, but handles them in its own way. From a developer's perspective, it has a better architecture (OOP instead of functional approach), stricter types handling and more comprehensive tests. From the point of view of a user, sinner offers additional features that Roop currently lacks.

:question: Is there a NSWF filter?<br/>
:exclamation: Nope. I don't care if you will do nasty things with sinner, it's your responsibility. And sinner is just a neutral tool, like a hammer or a knife, it is the responsibility of the user to decide how they want to use it.

:question: Is there a graphic interface?<br/>
:exclamation:Yes, but it still in development. You can start the program with `--gui` parameter to enable GUI.

:question: Can I use several execution providers simultaneously?<br/>
:exclamation: You can try. Seriously, you can set `--execution-provider cuda cpu`, and look, what will happen. May be it will work faster, may be it won't work at all. It is a large space for experiments.


## Credits

- [s0md3v](https://github.com/s0md3v/): the original author of roop
- [ffmpeg](https://ffmpeg.org/): for making video related operations easy
- [deepinsight](https://github.com/deepinsight): for their [insightface](https://github.com/deepinsight/insightface) project which provided a well-made library and models.
- [ARC Lab, Tencent PCG](https://github.com/TencentARC): for their [GFPGAN](https://github.com/TencentARC/GFPGAN) project which provided a face restoration library and models.
- and all developers behind libraries used in this project.

## License

GNU GPL 3.0