# sinner: sinner is non exactly roop

# Disclaimer

This is the rework of the [s0md3v/roop](https://github.com/s0md3v/roop/) that I'm working on for entertainment and educational purposes. It doesn't aim to be popular; it's just a fork made the way I want it to be.
The tasks that I aim to accomplish here are:

- :white_check_mark: Rewriting the code using OOP
- :white_check_mark: Provide a clear and easy API to make processing modules
- :white_check_mark: Support to different input and output data types, implemented over frame handlers
- :white_check_mark: Adding strict typing and static analysis on top of it
- :white_check_mark: In-memory processing without temporary frames
- :white_check_mark: Ability to continue processing after a stop
- :white_check_mark: Continuous processing chain
- :soon: Providing code coverage with tests
- :white_square_button: Do better swapping on rotated faces
- :white_square_button: Do face selection

## How do I install it?

The basic installation instructions for now are the same as those in the [s0md3v/roop](https://github.com/s0md3v/roop#how-do-i-install-it), check them out.
In short, you need to install python 3.9 or a later version, VC runtimes, and desired Execution Provider kit (depending on your hardware and OS).

## How do I use it?

Go to application folder and run `python run.py` with desired set of command-line parameters (or just pick one of the [example](/Command line usage examples) and make changes to suit your need).

Here is the list of all possible command-line parameters. 
```
  -h, --help            show this help message and exit
  --source SOURCE_PATH  select an source
  --target TARGET_PATH  select an target
  --output OUTPUT_PATH  select output file or directory
  --frame-processor {DummyProcessor,FaceEnhancer,FaceSwapper} [{DummyProcessor,FaceEnhancer,FaceSwapper} ...]
                        pipeline of frame processors
  --frame-handler {CV2VideoHandler,DirectoryHandler,FFmpegVideoHandler,ImageHandler}
                        frame engine
  --fps FPS             set output frame fps
  --keep-audio          keep original audio
  --keep-frames         keep temporary frames
  --many-faces          process every face
  --max-memory MAX_MEMORY
                        limit of RAM usage in GB
  --execution-provider {tensorrt,cuda,cpu} [{tensorrt,cuda,cpu} ...]
                        execution provider
  --execution-threads EXECUTION_THREADS
                        number of execution threads
  --in-memory           use in-memory processing
  --temp-dir TEMP_DIR   temp directory
```
* `--source`: the image file containing a face, which will be used for deepfake magic.
* `--target`: an image, a video file or a directory with png images for processing.
* `--output`: a path (either a file or a directory) to save the processing result. If not provided, the resulting file will be saved near the target with an automatically generated filename.
* `--frame-processor`: the frame processor module or modules, that you want to apply to your files. See the [built-in frame processors](/Built-in frame processors) section for the list of build-in modules and their possibilities.
* `--frame-handler`: a module to handle the `target`. In the most cases you should omit that parameter (sinner will figure it out itself).
* `--fps`: the parameter to set the frames per second (FPS) in the resulting video. If not provided, the resulting video FPS will have the same FPS as the `target` video (or 30, if an image directory has used as the `target`).
* `--keep-audio`: defaults to `true`. Keeps original audio in the resulting video.
* `--keep-frames`: defaults to `false`. Keeps processed frames in the `temp-dir` after finishing.
* `--many-faces`: defaults to `false`. If set to true, every frame processor in the processing chain will apply its magic to every face on every frame of the `target`. If set to `false`, just one face (just a first found, no heavy logic here) will be processed.
* `--max-memory`: defaults to `4` for Mac and `16` for any other platforms. Maximum amount of gigs of RAM, that will be allowed for sinner use.
**Note 1**: AI processing usually requires a significant amount of RAM. While processed, you will see the memory usage statistics, and the MEM LIMIT REACHED statistics indicates about lack of RAM.
**Note 2**: This parameter does not affect amount of used video RAM if GPU-accelerated `execution-provider` is used.
* `--execution-provider`: defaults to `cpu`. This parameter specifies what kind of driver should be used to produce AI magic, and it depends on what your hardware and software capabilities. The `cpu` provider should fit as a basic choice, but any GPU-accelerated option is worth to try.
* `--execution-threads`: defaults to `1`. Configures the count of parallel simultaneous processing tasks. This value heavily depends on your hardware capabilities — how much computing cores it have, and what amount of memory it can use. Let say, you have a CPU with 32 cores — so you can set `--execution-threads=32` and `--execution-provider=cpu` to use all its computing powers. Other case: a GPU with thousands of CUDA cores, which probably will be much faster in total, but one thread also will require a lot of those cores to work with. For that case I recommend to do some experiments, or wait while benchmark mode will be implemented to sinner.
* `--in-memory`: defaults to `true`. If set to true, all frames from the `target` will be extracted to memory by processor module request, without intermediate frames extraction. If set to false, all `target` frames will be extracted as a sequence of png files before processing (an 'old roop' way).
**Note**: this option does not affect memory usage, but it can have a slight influence to processing speed.
* `--temp-dir`: defaults to `temp` subdirectory in the application directory. A way to provide directory, where processed (and, in case of `--in-memory=false`, extracted too) frames will be saved.

## Built-in frame processors

There are modules, named frame processors, and each processor can do its own type of magic. You need to choose what frame processor (or processors)
you want to use, and give them some sources to work on. Here is the list of built-in frame processors: 
- `FaceSwapper`: does face swapping deepfake magic. Substitute a face from the `source` to a face (or faces) in the `target`. The processor is based on [insightface project example](https://github.com/deepinsight/insightface/blob/master/examples/in_swapper/inswapper_main.py) code.
![FaceSwapper demo](/demos/swapper-demo.gif)
- `FaceEnhancer`: does face restoration and enhancing quality magic on the `target`. The processor is based on libraries of [ARC Lab GFPGAN project](https://github.com/TencentARC/GFPGAN).
![FaceEnhancer demo](/demos/enhancer-demo.jpg)
- `DummyProcessor`: does literally nothing, it is just a test tool.

## Command line usage examples

```cmd
python run.py --source="d:\pictures\cool_photo.jpg" --target="d:\pictures\other_cool_photo.jpg" --frame-processor=FaceSwapper
```
Swaps one face on the `d:\pictures\other_cool_photo.jpg` picture to face from the `d:\pictures\cool_photo.jpg` picture and saves resulting image to `d:\pictures\cool_photo_other_cool_photo.png` (autogenerated name).
```cmd
python run.py --source="d:\pictures\cool_photo.jpg" --target="d:\videos\not_a_porn.mp4" --frame-processor FaceSwapper FaceEnhancer --output="d:\results\result.mp4" --many-faces --execution-provider=cuda
```
Swaps all faces on the `d:\videos\not_a_porn.mp4` video file to the face from `d:\pictures\cool_photo.jpg` and enhances all faces quality, both processing will be made using `cuda` provider, and result will be saved to the `d:\results\result.mp4`.
```cmd
python run.py --source="d:\pictures\any_picture.jpg" --target="d:\pictures\pngs_dir" --output="d:\pictures\pngs_dir\enhanced" --frame-processor=FaceEnhancer --many-faces --max-memory=24 --execution-provider=cuda --execution-treads=8
```
Enhances all faces on every png file in the `d:\pictures\pngs_dir` directory using `cuda` provider and 8 simultaneous execution threads, with limit of 24 Gb RAM, and saves every enhanced image to the `d:\pictures\pngs_dir\enhanced` directory. 
**Note 1**: only a png images supported for now.
**Note 2**: at this moment you should provide `source` even if it is not required by selected frame processor. 

## FAQ

:question: What are the differences between sinner and roop?<br/>
:exclamation: As said before, sinner has started as the fork of roop. It has the mostly same ideas, but differs in the approaches of how those idea should be made.
sinner uses the same ML libraries to do its magic, but treats them in its own way. From the point of view of a developer, it has a better architecture (OOP instead of functional approach),
more strict types handling and tests. From the point of view of an end user, there are features, which roop doesn't have at the current moment.

:question: Is there a NSWF filter?<br/>
:exclamation: Nope. I don't care if you will do nasty things with sinner, it's your responsibility. And sinner is just a tool, like a hammer or a knife.

:question: Is there a graphic interface?<br/>
:exclamation: At this moment there is no any GUI, but it is planned.

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