## ArgParseDirector
#### **A simpler, more powerful way to configure complex python scripts and tools**

**ArgParseDirector** is a drop-in replacement for python's ArgParse. It does everything ArgParse does and adds the following features:

* Configuration files. Merges command line and configuration file argument values.
* Supports configuration of argument values with code. ArgParseDirector configuration files are executable python.
* Supports the creation of arguments that are only available from the configuration file - not from the command line.
* Supports hierarchical arguments - multiple arguments passed as a group as a single entry in the parsed args.

ArgParseDirector is a simple extension of argparse that does all of the above with virtually no change to your current usage.

#### Why ArgParseDirector
There are a number of good script configuration tools available - both drop-ins for argparse and more sophisticated tools. So why another one? In order to get more power than the simpler drop-ins and avoid the complexity of the sophisticated tools:

* ArgParseDirector configuration files are just python. You already know how to write them. And you can generate a base file automatically.
* Executable configuration files make it easy to handle complex relationships between argument values.
* Having arguments not available from the command line allows flexibility without causing user confusion and error.
* Hierachical/group arguments simplify startup code.

#### Index
[Installation](#install)  
[Try it](#just-try-it)  
[Quick Intro](#quick-and-dirty-intro)  
[Summary](#summary)  
* [The parser](#the-parser-class)
* [Configuration files](#configuration-files)
* [The command line](#command-line-usage)
* [Matching and merging](#matching-and-merging-rules)
* [Using groups](#using-groups)  
* [Generating a config file](#generating-a-config-file)  

[Extended Intro](#extended-intro)  

#### Install
There are no dependencies outside of a standard python 3 installation. Type at the command line:

`pip install argparse-director`

#### Just try it
The easiest way to see how argparse_director works is to try it with some of your own argument configurations. Install argparse_director, grab one of your own scripts, and make the following changes:
1. Change import, parser construction lines. And instead of starting your script, just print out the args:
```
from argparse_director import ArgParseDirector, Namespace, rec_print  # original: from argparse import ArgumentParser, Namespace
...
parser = ArgParseDirector()    # original: parser = ArgumentParser()
...                            # same add_argument()
args = parser.parse_args()     # same parser_args()

# dont run the script - just print out args - we ARE experimenting here!
print(args)                    # original: something like main(args) or start(args) - you know what to do
```
2. Now run it, and look at the what gets printed:
```
> ./yourscript
Namespace(yourarg=value, yourarg2=value, ...)
```
3. Next generate a configuration file. After the line that prints your args add this:
```
# generate config file
parser.gen_config_file('trial_config.py')

```
Run it, and then comment out the `parser.gen_config_file()` line - you don't want to keep remaking a base line config file!  

Take a look at 'trial_config.py'. You will see that 3 python dictionaries have been created for you. Edit a few of the values in `config_args`, and run the script like this:
```
> ./yourscript --config_path trial_config.py
Namespace(yourarg=value, yourarg2=value, ...)
```
You'll see that Namespace has your defaults, but has picked up the values from 'trial_config.py' - because you told it to with `--config_path trial_config.py` on the command line.  

4. Fool around  
Experiment with this ... try some of your args from the command line, and edit some of them in 'trial_config.py'.  
The command line overrides the configuration file, and the configuration file overrides the defaults set in `add_argument()`.  
Add arguments to `config_args` to create args to your script that you can change in config, but users cannot change from the command line. Add python code to automatically set values, enforce related items or create args ... you will quickly see how this works.  
Try `rec_print()` if you like. It pretty prints dictionaries and Namespaces - handy if you have a lot arguments.  
That's it - this isn't rocket science.
  
Best to stay away from `config_groups` and `config_required` until you read a little more.


#### Quick and Dirty Intro
This is a quick but less experimental way to get acquainted - there is an [extended intro](#extended-intro) below, as well.  

* Change import and parser construction names.
* Use same `parser.add_argument()` calls.
```
from argparse_director import ArgParseDirector

parser = ArgParseDirector()
parser.add_argument('--opt1',    default=25, type=int, arg_group='group1')
parser.add_argument('positional',            type=int)
```
Notice new option `arg_group`. Each argument with this option is returned from `parse_args()` in the main Namespace, and in a separate Namespace with just that group's arguments. Arguments can be assigned to more than one group by sett `arg_group` with a tuple of name strings: `arg_group=('group1', 'group2')`.

Configuration files are straightforward: each has up to 3 python dictionaries: 1 each for arg configuration, group creation and required/positional args. None are mandatory - but if you have them they **MUST** be named `config_args`, `config_groups` and `config_required`, respectively. You can add any python code you like.
```
# use arbitrary python as needed
value1 = 123
value2 = 128 if value1<128 else 256

# for setting command line arg options or creating new arguments only for config file ...
config_args = {
    'opt1' : value1,    # actual value and type not a string
    'opt2' : value2,    # only usable from config file as there was no `add_argument()` for it
}

# for gathering args into groups
config_groups = {
    'group1' :  ['opt1', 'opt2'],
    'group2' :  ['opt1']
}

# for positional args
config_required = {
    'positional' :    123456
}
```
Invoke the configuration file from command line or in `parse_args()` call:
```
>./script.py 123456 --config_path config_file.py
or
>./script.py
with ...
parser.parser_args(config_path='config_file.py')

generates:
Namespace(group1=Namespace(opt1=123, opt2=128), group2=Namespace(opt1=123), opt1=123, opt2=128, positional=123456))
```
Required arguments are positional, as with argparse - they have to come immediately after script name.
```
>./script.py 54321 --config_path config_file.py
Namespace(group1=Namespace(opt1=123, opt2=128), group2=Namespace(opt1=123), opt1=123, opt2=128, positional=54321)
```
* Use `add_argument()` as always, with additional `arg_group='group_name'` option to create groups. Create as many groups as you need. An argument can belong to more than one group - 'arg_group' can be a single group name or a tuple of group names.
* Invoke from command line as always, with additonal `--config_path='config_file'`:
    * `scriptname positional_args --config_path config_file optional_command_line_arguments`
    * Positional arguments must immediately follow script name before '--config_path'.
    * `--config_path` on the command line is optional - you can use `parser_args(config_path='config_file.py')` if you prefer.
    * If you use neither, no config file will be used.
* Command line overrides config file, config file overrides defaults. Use them all as needed.
* Generate a baseline config file from parser with `parser.gen_config_file('file_name')`.
* Config files are run with `exec()` - so use python code as you need in config file to enforce relationships, calculate values, even add arguments.

### Summary
##### The module:  
Install with `pip install argparse-director`  
Import usually with `from argparse_director import ArgParseDirector, rec_print`  
Contains `ArgParseDirector` parser creation class, and function `rec_print()` for pretty printing Dictionaries and Namespaces

##### The parser class
**ArgParseDirector** is called just like **ArgumentParse**:
* `parser = ArgParserDirector()`
* It does not add or alter any arguments. It does create 2 additional functions, and adds arguments to 2:


**`parser.add_argument()`** supports one additional argument `arg_group`, which takes a single group name string, or tuple of group name strings:  
* `parser.add_argument('test', arg_group='work_group')`  
* All arguments with the same group name are collected in their own Namespace which is included in the main argument Namespace returned by `parse_args()`


**`parser.parse_args()`** supports one additional argument `config_path`, which takes a string with the full path and file name of the configuration file to use.
* `config_path` is optional - if omitted, the config path and file should be set on the command line with `--config_path 'path/config_file'`


**`parser.gen_config_file(fname, prefix='    ')`**
* This is a new function which generates a configuration file.
* `fname` is a full path and file name to write the configuration file.
    * If `fname` already exists, the user is prompted before overwriting.
* `prefix` is a string used to indent entries into each of the configuration dictionaries. The default is 4 spaces.

**`parser.get_config_file_name()`**
* This is a new function which returns the full path and name of the configuration file.
* It will return None if no file was used: if one was not specified, or the specified file did not exist.


#### Configuration files
* Configuration files consist of up to 3 dictionaries. All are optional, but if present, they must have the names noted here.
* **`config_args`** is the name of the optional dictionary used to configure typical argparse arguments: those that lead with a prefix, and have a default if no value is entered on the command line.
    * Each **key** in the dictionary is the argument name, less any prefix.
    * Each **value** is the value for that argument. Just use the actual python value for this - not a string representation
    * You do NOT have to have a `config_args` entry for each argument added with `add_argument()`. If omitted, the default or command line value will be used.
    * You CAN have `config_args` entries that have not been added with `add_argument()`. This allows flexibility, while not cluttering up the command line or confusing users.
    ```
    config_args = {
        'opt1' : 52,
        'opt2' : True
    }
    ```
    * If no `config_args` dictionary is present, the value entered for the command line will be used if entered, or the default from `add_argument()`

* **`config_groups`** is the name of the optional dictionary used to configure groups.  
    * Each **key** in the dictionary is a group name.  
    * Each **value** is a list of strings of the names of the arguments that are members of this group, one string per argument name.  
    * You do NOT have to have a `config_groups` entry for all the groups created with `add_argument()`.  
    * You CAN have `config_groups` entries that have not been added with `add_argument()`.  
    ```
    config_groups = {
        'personal' : ['age', 'salary', 'bonus'],
        'work'     : ['salary, 'bonus', 'job_title']
    }
    ```

    * If no `config_groups` dictionary is present, the groups created with `add_argument()` remain unchanged.  

 * **`config_required`** is the name of the optional dictionary used to configure required/positional arguments.  
    * Each **key** in the dictionary is the argument name.  
    * Each **value** is the value for that argument. Just use the actual python value for this - not a string representation.  
    * **Unlike the other dictionaries**, if you have a `config_required` dictionary, it MUST have all the positional arguments created with `add_argument()`, and may NOT have any additions.

    ```    
    config_required = {

        'must1' : 52,
        'must2' : True
    }
    ```
    * If no `config_args` dictionary is present, the values entered on the command line will be used.  
    * The order in this dictionary is not critical - though they are positional, argparse_director finds them by name if needed to fill missing command line values. This does NOT change the fact that they need to be in order on the command line.

#### Command line usage
* The command line with argparse_director operates essentially the same as with argparse:
```
> ./script_name.py posval1 posval2 --arg1 val1 --arg2 val2
```
Specifying which configuration file to use works as if you had created an argument for it named `--config_path`:
```
> ./script_name.py --arg1 val1 --arg2 val2 --config_path path/to/config_file
```
`--config_path` can appear anywhere on the command line that optional arguments are legal. This is anywhere after any defined positional arguments.  
`--config_path` is created by ArgParseDirector, and it does not appear in the args Namespace - like '--help'. If you need to get the file name, see `get_config_file_name()`
   
#### Matching and merging rules
* For typical options, command line overrides the configuration file, and the configuration file overrides the defaults.
* For groups, they are merged. Whatever groups you define in `add_argument()` calls are added to whatever groups you defined in the configuration file. There is no way to delete a group member other than not adding it in the first place.
* Positional arguments are a little tricker. Positional arguments must be in the command line immediately following the script name, in the order they were added to the parser. This doesn't change when using a configuration file. You can enter them on the command line, of course, or let the configuration file set them.
    * If you enter some but not all positional args on the command line, the command line values are applied starting with the first position, and proceeding in order until there are no more. Any missing at the end are supplied from the configuration file.

#### Using groups
Grouping arguments allows the organization of arguments into simple subsets that can be passed as a single name. This makes it simpler to organize the initialization of a class or subsystem, to create a set of arguments for saving, to narrow the interface to a class or function, and to ensure that only the appropriate info is passed where needed.

Arguments can be in multiple Namespaces, and they always also remain in the main Namespace returned by `parse_args()`. At this time Namespaces can not be members of other Namespaces other than the main one.

To show an example, machine learning systems often separate the tunable parameters of a model into a set of hyperparameters. The search for the right combination of these values is a critical and difficult task. Being able to get, pass, and save these as a single entity saves a lot of time and confusion. Imagine a simplified model with the following return from `parse_args()`
```
print(args)
Namespace(ask_permission=True, back_end='ddp', batch_size=16, ckpt_path=None, config_path='confg_11p.py', debug=False, epochs=350, exit_to_python=False, f0=32, f1=32, f2=64, f3=16, f4=32, f5=32, f6=64, f7=64, gpus='0 1 2 3 4 5', hparams=Namespace(back_end='ddp', batch_size=16, f0=32, f1=32, f2=64, f3=16, f4=32, f5=32, f6=64, f7=64, gpus='0 1 2 3 4 5', hy=10, i0=16, i1=16, i2=16, i3=16, init_class_param=1.0, init_inst_param=1.0, learn_class_parameters=False, learn_inst_parameters=True, lr=0.002, lr_class_param=0.1, lr_inst_param=0.1, p0=128, p1=128, p2=256, pct_data=1.0, skip_clamp_data_param=False, wd=0.0008, wd_class_param=0.0, wd_inst_param=0.0, wx=10), hy=10, i0=16, i1=16, i2=16, i3=16, init_class_param=1.0, init_inst_param=1.0, interactive=True, learn_class_parameters=False, learn_inst_parameters=True, log_flags='ebt', log_root='/home/seth/dev/pytorch_logs/', log_tag=-1, lr=0.002, lr_class_param=0.1, lr_inst_param=0.1, msg_level='v', net_desc='02: 10x10 ckpt:569 val_pre .649 test: rec 0.6472 pre 0.6445 acc 0.9866: 550e  \n', net_history='00: lr .002, wd .0008, 9x9 lip t, lcp f ckpt: 298/pv .792: test rec 0.8584 pre 0.8514 acc 0.9767: 392e  BEST operationally \n01: 9x9 to see if repeatable: ckpt: 334 vp .827  test: rec 0.8266 pre 0.8168 acc 0.9536: 350e  better numbers than 00 but not as good operationally  \n', p0=128, p1=128, p2=256, pct_data=1.0, plot_conf=True, port=10000, print_model=False, report_flags='bt', skip_clamp_data_param=False, wd=0.0008, wd_class_param=0.0, wd_inst_param=0.0, wx=10)
```
A lot of parameters, and this is not a particularly complex model. That's why a number are marked as members of group `hparams`.
```
print(args.hparams)

Namespace(back_end='ddp', batch_size=16, f0=32, f1=32, f2=64, f3=16, f4=32, f5=32, f6=64, f7=64, gpus='0 1 2 3 4 5', hy=10, i0=16, i1=16, i2=16, i3=16, init_class_param=1.0, init_inst_param=1.0, learn_class_parameters=False, learn_inst_parameters=True, lr=0.002, lr_class_param=0.1, lr_inst_param=0.1, p0=128, p1=128, p2=256, pct_data=1.0, skip_clamp_data_param=False, wd=0.0008, wd_class_param=0.0, wd_inst_param=0.0, wx=10)
```
Still a lot, but much more managable.  

By using groups to collect all these arguments, we gain an easy way to initialize the model, save this training session's important information, and pass the parameters to a routine that will do a search of values to find the best combination.

Groups are simply new argparse Namespaces. Because the keys and values are copied into each Namespace, changes to any arg values are limited to the Namespace they are in: changing `arg.back_end` will not change `arg.hparams.back_end`. It can be useful/tempting to change arg values as they are processed. Remember, when passing a Namespace as a function argument, python will pass it by reference - so changing a value in the passed Namespace will change that value in all references to that Namespace.

#### Generating a config file
You can generate a initial configuration file from the parser you created with `add_arguments()` using `parser.gen_config_file(file_name)`. This will write a file named `file_name` with the appropriate dictionaries for your parser.

A realistic example - here are the `add_argument()` calls to configure and train a machine learning model:

```
# type conversion function used below
def strToBool(s, d=['t', 'T', 'true',  'True', 'y', 'Y']):
    return s in d

parser = ArgParseDirector()

parser.add_argument("--ckpt_path",              default=None,                                                           type=str,       help="full path to checkpoint to load")

parser.add_argument("--epochs",                 default=10,                                                             type=int,       help="number of epochs")
parser.add_argument("--batch_size",             default=16,                                     group_arg=hparams,      type=int,       help="size of the batches per gpu")
parser.add_argument("--gpus",                   default='0 1 2 3',                              group_arg=hparams,      type=str,       help="device numbers of gpus to use")
parser.add_argument("--back_end",               default='ddp',                                  group_arg=hparams,      type=str,       help="distributed back end",                                        choices=['dp', 'ddp'])
parser.add_argument("--port",                   default=10000,                                                          type=int,       help="port for ddp ipc: must be greater than 10000")
parser.add_argument("--log_root",               default='/home/dev/pytorch_logs/',                                      type=str,       help="root path for logs")
parser.add_argument("--log_flags",              default='ebt',                                                          type=str,       help="log control: e, b, t signal epoch, batch, test reporting")
parser.add_argument("--log_tag",                default=-1,                                                             type=int,       help="reset log tag, must be >= 0")
parser.add_argument("--pct_data",               default=1.0,                                    group_arg=hparams,      type=float,     help="set percentage of data to use - for quick testing")
parser.add_argument("--wx",                     default=7,                                      group_arg=hparams,      type=int,       help="number of classes in w or x or dimension")
parser.add_argument("--hy",                     default=7,                                      group_arg=hparams,      type=int,       help="number of classes in h or y or dimension")
parser.add_argument("--lr",                     default=.001,                                   group_arg=hparams,      type=float,     help="learning rate")

parser.add_argument("--msg_level",              default='v',                                                            type=str,       help="messaging level (v)erbose, (q)uiet, (d)ebug, (s)ilent",       choices=['v', 'q', 's'])
parser.add_argument("--report_flags",           default='bt',                                                           type=str,       help="report control: e, b, t signal epoch, batch, test reporting")
parser.add_argument("--plot_conf",              default='true',                                                         type=strToBool, help="plot confusion matrix")
parser.add_argument("--debug",                  default='false',                                                        type=strToBool, help="enable debug() messaging")
parser.add_argument("--print_model",            default='false',                                                        type=strToBool, help="print model summary during startup")

# added for ml data param learning
parser.add_argument('--learn_class_parameters', default='true',                                 group_arg=hparams,      type=strToBool, help='Learn temperature per class')
parser.add_argument('--learn_inst_parameters',  default='true',                                 group_arg=hparams,      type=strToBool, help='Learn temperature per instance')
parser.add_argument('--skip_clamp_data_param',  default='false',                                group_arg=hparams,      type=strToBool, help='Do not clamp data parameters during optimization [f, F, false, False, t, T, true, True]')
parser.add_argument('--lr_class_param',         default=0.1,                                    group_arg=hparams,      type=float,     help='Learning rate for class parameters')
parser.add_argument('--lr_inst_param',          default=0.1,                                    group_arg=hparams,      type=float,     help='Learning rate for instance parameters')
parser.add_argument('--wd_class_param',         default=0.0,                                    group_arg=hparams,      type=float,     help='Weight decay for class parameters')
parser.add_argument('--wd_inst_param',          default=0.0,                                    group_arg=hparams,      type=float,     help='Weight decay for instance parameters')
parser.add_argument('--init_class_param',       default=1.0,                                    group_arg=hparams,      type=float,     help='Initial value for class parameters')
parser.add_argument('--init_inst_param',        default=1.0,                                    group_arg=hparams,      type=float,     help='Initial value for instance parameters')

parser.add_argument("--exit_to_python",         default='false',                                                        type=strToBool, help="exit to python")
parser.add_argument("--ask_permission",         default='true',                                                         type=strToBool, help="ask user for permission to start, erase logs")
parser.add_argument("--interactive",            default='true',                                                         type=strToBool, help="poll for input during training")
```
There are many more configurable arguments needed, so a config file is a good idea. Hand creating it is straightforward, but tedious. Let's use `parser.gen_config_file('ml_config.py')` to generate the following baseline file:

```
# ArgParseDirector configuration file 'ml_config.py': original generated 2020-04-13 09:32:31
# 'ml_config.py may be edited to:
#   add/change entries and values in config_args,
#   add/change group names and keys in config_groups,
#   change values for positional args in config_required
#   or add python code as needed

# config_args: original generated from all args added with add_argument()
# change values to override defaults, add keys to create arguments that will be returned from parse_args() but not available from command line
# do not change dictionary name 'config_args'
config_args = {
    'ckpt_path' :                None,
    'epochs' :                   10,
    'batch_size' :               16,
    'gpus' :                     '0 1 2 3',
    'back_end' :                 'ddp',
    'port' :                     10000,
    'log_root' :                 '/home/dev/pytorch_logs/',
    'log_flags' :                'ebt',
    'log_tag' :                  -1,
    'pct_data' :                 1.0,
    'wx' :                       7,
    'hy' :                       7,
    'lr' :                       0.001,
    'msg_level' :                'v',
    'report_flags' :             'bt',
    'plot_conf' :                True,
    'debug' :                    False,
    'print_model' :              False,
    'learn_class_parameters' :   True,
    'learn_inst_parameters' :    True,
    'skip_clamp_data_param' :    False,
    'lr_class_param' :           0.1,
    'lr_inst_param' :            0.1,
    'wd_class_param' :           0.0,
    'wd_inst_param' :            0.0,
    'init_class_param' :         1.0,
    'init_inst_param' :          1.0,
    'exit_to_python' :           False,
    'ask_permission' :           True,
    'interactive' :              True,
}

# config_groups: from all args added with add_argument() call that includes 'arg_group = 'some_group_name' or ('group1', 'group2')
# add names to lists, or create new groups
# do not change dictionary name 'config_groups'
config_groups = {
    'hparams' : [
        'batch_size',
        'gpus',
        'back_end',
        'pct_data',
        'wx',
        'hy',
        'lr',
        'learn_class_parameters',
        'learn_inst_parameters',
        'skip_clamp_data_param',
        'lr_class_param',
        'lr_inst_param',
        'wd_class_param',
        'wd_inst_param',
        'init_class_param',
        'init_inst_param',
    ],
}

# required arguments: from all args added as positional with add_argument()
# change values, do NOT remove or add any entries
# do not change dictionary name 'config_required'
config_required = {
}
```

The file can be edited to support organization and usage: renaming, reformatting, recording history, enforcing model relationships, extending arguments needed:
```
# config file for gaze_llp
# added: sn just after generation date/time above
# values used to compute model sizes    # original values (pre 11l)
_f1         = 32                        # 64
_f3         = 16                        # 128
_f5         = 32                        # 256
_p0         = 128                       # 128
fname       = '/home/dev/pytorch_work/config_11p.py'

# command line plus additional args
config_args = {

    # history - at top for convenience
    "net_history" :               "00: lr .002, wd .0008, 9x9 lip t, lcp f ckpt: 298/pv .792: test rec 0.8584 pre 0.8514 acc 0.9767: 392e  BEST operationally \n" +\
                                  "01: 9x9 to see if repeatable: ckpt: 334 vp .827  test: rec 0.8266 pre 0.8168 acc 0.9536: 350e  better numbers than 00 but not as good operationally  \n",

    "net_desc" :                  "02: 10x10 ckpt:569 val_pre .649 test: rec 0.6472 pre 0.6445 acc 0.9866: 550e  \n",

    # hparams
    # basic for trainer and data construction
    'batch_size' :               16,
    'lr' :                       0.002,
    'wd' :                       0.0008,
    'wx' :                       10,
    'hy' :                       10,

    # data param learning
    'learn_class_parameters' :   False,
    'learn_inst_parameters' :    True,
    'skip_clamp_data_param' :    False,
    'lr_class_param' :           0.1,
    'lr_inst_param' :            0.1,
    'wd_class_param' :           0.0,
    'wd_inst_param' :            0.0,
    'init_class_param' :         1.0,
    'init_inst_param' :          1.0,

    # model configuration parameters: cannot be changed from command line
    # calculated from vars above           # original values (pre 11l)
    'f0' :                        32,      # 64
    'f1' :                        _f1,     # 64
    'f2' :                        _f1*2,   # 128
    'f3' :                        _f3,     # 128
    'f4' :                        _f3*2,   # 256
    'f5' :                        _f5,     # 256
    'f6' :                        _f5*2,   # 512
    'f7' :                        64,      # 256
    'i0' :                        16,      # 16
    'i1' :                        16,      # 32
    'i2' :                        16,      # 32
    'i3' :                        16,      # 32
    'p0' :                        128,     # 128
    'p1' :                        _p0,     # 64
    'p2' :                        _p0*2,   # 512 

    # required to construct trainer
    'gpus' :                     '0 1 2 3 4',
    'back_end' :                 'ddp',
    'pct_data' :                 1.0,
    # end hparams

    # training basics
    'epochs' :                   100,
    'port' :                     10000,

    # files: configuration, checkpoint to load
    'config_path' :              'confg_11p.py',
    'ckpt_path' :                None,

    # logging: file, file tag, flags
    'log_root' :                 '/home/seth/dev/pytorch_logs/',
    'log_tag' :                  -1,
    'log_flags' :                'ebt',

    # reporting
    'msg_level' :                'v',
    'report_flags' :             'bt',
    'plot_conf' :                True,
    'debug' :                    False,
    'print_model' :              False,

    # interacting with end user
    'exit_to_python' :           False, # exit to python at completion
    'ask_permission' :           True,  # ask permission to delete files, etc
    'interactive' :              True,  # interact during training through RunMonitor
}
```
This config file and the original parser it was generated from work together, as you already know
```
> ./realistic.py --config_path config_llp.py --epochs 350 --gpus '0 1 2 3 4 5'
Namespace(ask_permission=True, back_end='ddp', batch_size=16, ckpt_path=None, config_path='confg_11p.py', debug=False, epochs=350, exit_to_python=False, f0=32, f1=32, f2=64, f3=16, f4=32, f5=32, f6=64, f7=64, gpus='0 1 2 3 4 5', hparams=Namespace(back_end='ddp', batch_size=16, f0=32, f1=32, f2=64, f3=16, f4=32, f5=32, f6=64, f7=64, gpus='0 1 2 3 4 5', hy=10, i0=16, i1=16, i2=16, i3=16, init_class_param=1.0, init_inst_param=1.0, learn_class_parameters=False, learn_inst_parameters=True, lr=0.002, lr_class_param=0.1, lr_inst_param=0.1, p0=128, p1=128, p2=256, pct_data=1.0, skip_clamp_data_param=False, wd=0.0008, wd_class_param=0.0, wd_inst_param=0.0, wx=10), hy=10, i0=16, i1=16, i2=16, i3=16, init_class_param=1.0, init_inst_param=1.0, interactive=True, learn_class_parameters=False, learn_inst_parameters=True, log_flags='ebt', log_root='/home/seth/dev/pytorch_logs/', log_tag=-1, lr=0.002, lr_class_param=0.1, lr_inst_param=0.1, msg_level='v', net_desc='02: 10x10 ckpt:569 val_pre .649 test: rec 0.6472 pre 0.6445 acc 0.9866: 550e  \n', net_history='00: lr .002, wd .0008, 9x9 lip t, lcp f ckpt: 298/pv .792: test rec 0.8584 pre 0.8514 acc 0.9767: 392e  BEST operationally \n01: 9x9 to see if repeatable: ckpt: 334 vp .827  test: rec 0.8266 pre 0.8168 acc 0.9536: 350e  better numbers than 00 but not as good operationally  \n', p0=128, p1=128, p2=256, pct_data=1.0, plot_conf=True, port=10000, print_model=False, report_flags='bt', skip_clamp_data_param=False, wd=0.0008, wd_class_param=0.0, wd_inst_param=0.0, wx=10)
```
ArgParseDirector includes a `rec_print()` function to cope with Namespaces like this:
```
rec_print(args)

hparams :

    gpus :                     '0 1 2 3 4 5'
    p2 :                       256
    learn_inst_parameters :    True
    lr_inst_param :            0.1
    p0 :                       128
    wd_inst_param :            0.0
    f5 :                       32
    i0 :                       16
    i1 :                       16
    skip_clamp_data_param :    False
    init_inst_param :          1.0
    f2 :                       64
    f3 :                       16
    lr :                       0.002
    wd :                       0.0008
    hy :                       10
    f0 :                       32
    f6 :                       64
    back_end :                 'ddp'
    wd_class_param :           0.0
    batch_size :               16
    f4 :                       32
    p1 :                       128
    lr_class_param :           0.1
    f1 :                       32
    i2 :                       16
    pct_data :                 1.0
    init_class_param :         1.0
    f7 :                       64
    learn_class_parameters :   False
    i3 :                       16
    wx :                       10

gpus :                         '0 1 2 3 4 5'
msg_level :                    'v'
p2 :                           256
learn_inst_parameters :        True
lr_inst_param :                0.1
p0 :                           128
wd_inst_param :                0.0
f5 :                           32
i0 :                           16
i1 :                           16
ask_permission :               True
skip_clamp_data_param :        False
init_inst_param :              1.0
interactive :                  True
f2 :                           64
f3 :                           16
print_model :                  False
debug :                        False
lr :                           0.002
wd :                           0.0008
hy :                           10
config_path :                  'confg_11p.py'
epochs :                       350
f0 :                           32
f6 :                           64
back_end :                     'ddp'
wd_class_param :               0.0
batch_size :                   16
plot_conf :                    True
f4 :                           32
p1 :                           128
lr_class_param :               0.1
f1 :                           32
net_desc :                     '02: 10x10 ckpt:569 val_pre .649 test: rec 0.6472 pre 0.6445 acc 0.9866: 550e  
'
port :                         10000
log_root :                     '/home/seth/dev/pytorch_logs/'
i2 :                           16
pct_data :                     1.0
exit_to_python :               False
ckpt_path :                    None
init_class_param :             1.0
net_history :                  '00: lr .002, wd .0008, 9x9 lip t, lcp f ckpt: 298/pv .792: test rec 0.8584 pre 0.8514 acc 0.9767: 392e  BEST operationally 
01: 9x9 to see if repeatable: ckpt: 334 vp .827  test: rec 0.8266 pre 0.8168 acc 0.9536: 350e  better numbers than 00 but not as good operationally  
'
f7 :                           64
report_flags :                 'bt'
learn_class_parameters :       False
i3 :                           16
log_tag :                      -1
log_flags :                    'ebt'
wx :                           10
```

#### Extended Intro
Let's start with a simple example.

*By the way, this is not a tutorial about argparse - it assumes you are at least a little familiar with argparse.*

#### Just like argparse
Imagine an example script named 'example.py'. Using argparse_director is just like argparse, with the obvious import and class name changes:
```
#!/bin/exe/python3
# example.py - argparse_director example

# import from argparse_director instead of argparse
from argparse_director import ArgParseDirector

# create parser and define 3 arguments: use ArgParseDirector() instead of ArgumentParser()
parser = ArgParseDirector()
parser.add_argument("--name",       default='john doe',      type=str)
parser.add_argument("--age",        default=25,              type=int)
parser.add_argument("--occupation", default='web developer', type=str)

# parse the command line and print the resulting args
args = parser.parse_args()
print(args)
```
From the command line:
```
> ./example.py
> Namespace(age=25, name='john doe', occupation='web developer')
```
The Namespace shows the defaults for each argument as expected.

#### Configuration files contain python dictionaries
A configuration file for these arguments is a python dictionary with one key for each argument. The key is a string without the command line prefix. The  value is the actual value - not  a string representation. You can simply write it as you would any python file. Later on, we'll see how to automatically generate a complete configuration files based on what has been added with `add_parser()`.
```
# config file basic_config.py
# create a dictionary named 'config_args' - this name is required!
config_args  = {
    'name' :        'jane doe',
    'age'  :        23,
    'occupation' :  'vp, web development'
}
```
The file is normal python, defining a dictionary of keys as arguments and their values. The dictionary **must** be named `config_args`, and each entry configures one argument. Notice that each key/argument does not have the prefix required to enter it on the command line, and each value is the actual type of the argument value.

Using the configuration file is straightforward. Assume this one is called 'basic_config.py'. It can be named anything you want to, and it does not have to have '.py', or any extension. Invoke from the command line by specifying the configuration file like this:
```
> ./example.py --config_path basic_config.py
Namespace(age=23, name='jane doe', occupation='vp, web development')
```
The `--config_path` argument is added for you by argparse_director, like `--help` is by argparse. And like `--help`, you won't see it in the args returned to you.
Notice that printed values are the values from the configuration file, **not** from defaults in the `add_argument()` calls. The configuration file values override the defaults.

We can use the command line along with configuration file:
```
> ./example.py --config_path basic_config.py --age 24
Namespace(age=24, name='jane doe', occupation='vp, web development')
```
#### Defaults, configuration files and command line arguments work together
Command line values override the configuration file values and the defaults. The rules are simple:
* Argument defaults are used if nothing changes them.
* Any argument specified in the configuration file overrides it's default.
* Any argument on the command line overrides the the configuration file and the default.

The configuration file does not have to have an entry for every command line argument:
```
# config file basic_config.py
# create a dictionary named 'config_args' - this name is required!
config_args  = {
    'name' :        'jane doe',
    'occupation' :  'vp, web development'
}
```
```
> ./example.py --config_path basic_config.py
Namespace(age=25, name='jane doe', occupation='vp, web development')
```
The 'name' and 'occupation' args came from the file, 'age' from the defaults. And of course, any of these could have been overridden from the command line.

Similarly, the config file can have arguments that are not available from the command line:
```
# config file basic_config.py
# create a dictionary named 'config_args' - this name is required!
config_args  = {
    'name' :        'jane doe',
    'occupation' :  'vp, web development',
    'salary' :      125,000
}
```
```
> ./example.py --config_path basic_config.py
Namespace(age=25, name='jane doe', occupation='vp, web development', salary=125,000)
```
Trying to use `--salary` from the command line fails ... it is only defined and set by the config file.

This is one of the many good reasons to use configuration files - to have configurable arguments that you do not have to hand enter with `add_argument()`, that do not clutter up the command line, and that cannot be altered by an end user.


#### Configuration files are python
The config file is executed with `exec()` as standard python - so it can contain code to set values, create keys, etc:
```
# config file basic_config.py
# create a dictionary named 'config_args' - this name is required!
# set a conditional value
occupation   = 'vp, marketing'
config_args  = {
    'name' :        'jane doe',
    'occupation' :  occupation,
    # set a conditional value
    'salary' :      125000 if occupation=='vp, web development' else 95000
}

# create a conditional argument
if occupation == 'vp, marketing':
    config_args['bonus']    = 30000
```
```
> ./example.py --config_path basic_config.py
Namespace(age=25, bonus=30000, name='jane doe', occupation='vp, marketing', salary=95000)
```

#### Creating argument groups
ArgParseDirector can group any arguments you choose under any name you choose. Groups can be defined with `add_argument()` using the keyword `arg_group`:
```
#!/bin/exe/python3
# example.py - argparse_director example

# import from argparse_director instead of argparse
from argparse_director import ArgParseDirector

# create parser and define 3 arguments: use ArgParseDirector() instead of ArgumentParser()
parser = ArgParseDirector()
parser.add_argument("--name",       default='john doe',      type=str, arg_group='personal')
parser.add_argument("--age",        default=25,              type=int)
parser.add_argument("--occupation", default='web developer', type=str, arg_group='personal')
parser.add_argument("--bugs",       default='wrong colors',  type=str, arg_group='work')
parser.add_argument("--new module", default='security',      type=str, arg_group='work')

# parse them and print out args, and the arg_groups
args    = parser.parse_args()
print('args = ', args)
print()
print('personal = ', args.personal)
print('work     = ', args.work)
```
```
> ./example.py --config_path basic_config.py
args =  Namespace(age=25, bonus=30000, bugs='wrong colors', name='jane doe', new_module='security', occupation='vp, marketing', personal=Namespace(name='jane doe', occupation='vp, marketing'), salary=95000, work=Namespace(bugs='wrong colors', new_module='security'))

personal =  Namespace(name='jane doe', occupation='vp, marketing')
work     =  Namespace(bugs='wrong colors', new_module='security')
```
The returned args contains 2 additional arguments, both Namespaces: 'personal' and 'work'. The value for each is a Namespace that contains only the arguments and values for that arg_group, as defined in `add_argument()`. Note that the grouped args are available **in both the group and in args Namespaces**.

Groups can also be created with a config file by adding a dictionary with the required name `config_groups`. For each entry in `config_groups`, the key is a string that names the group, and value is a list of of strings naming the arguments to be included in the group:
```
# config file basic_config.py
# create a dictionary named 'config_args' - this name is required!
occupation   = 'vp, marketing'
config_args  = {
    'name' :        'jane doe',
    'occupation' :  occupation,
    'salary' :      125000 if occupation=='vp, web development' else 95000
}
if occupation == 'vp, marketing':
    config_args['bonus']    = 30000

# create a dictionary named config_groups - if you configure groups this name is required
config_groups = {
    'personal' : ['age'],
    'work' :     ['bugs', 'new_module', 'occupation']
}
```
```
> ./example.py --config_path basic_config.py
args =  Namespace(age=25, bonus=30000, bugs='wrong colors', name='jane doe', new_module='security', occupation='vp, marketing', personal=Namespace(age=25, name='jane doe', occupation='vp, marketing'), salary=95000, work=Namespace(bugs='wrong colors', new_module='security', occupation='vp, marketing'))

personal =  Namespace(age=25, name='jane doe', occupation='vp, marketing')
work     =  Namespace(bugs='wrong colors', new_module='security', occupation='vp, marketing')
```
The groups defined by `add_argument()` and the config file are **merged**. The config file just adds 'age' to the 'personal' group, while 'work' has been completely restated in the config file. Both approaches work fine. Note that 'occupation' is a member of both groups: it was added to 'personal' in `add_argument()` and to 'work' in the config file.



