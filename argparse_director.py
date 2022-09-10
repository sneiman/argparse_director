# class for generating command line, and configuration files:
# a replacement for arparser, it performas all the same functions with several key differences
# 1: can use an editable configuration file to set all or some arguments, allowing cmdline entries to take precedence if present
# 2: it can generate Namespace args: a single entry in parser_args() return that hold multiple argument values. To create, im add_argument() use 'param="group name"'
# 3: arguments not available at the cmdline can be added to the config file.
# 4: the config file can run arbitrary python code as needed to generate arguments and their values
import os
import re
import sys
import datetime
from   argparse import ArgumentParser, Namespace


# check arguments for type
def check_arg(arg, req_type, def_value=None, item_type=None, caller_name=None, item_test=None):

    result  = def_value
    if arg is not None:
        if isinstance(arg, req_type):
            if isinstance(arg, (list, tuple)):
                if all(isinstance(v, item_type) for v in arg):
                    result  = arg
                else:
                    raise TypeError(f"{caller_name if caller_name is not None else 'check_arg()'}: args items must all be {item_type}")
            else:
                result = arg
        else:
            raise TypeError(f"{caller_name if caller_name is not None else 'check_arg()'}: arg must be {req_type}")

    return result


# recursively determine longest key length with prefix
def rec_key_len(d, prefix_len=0, maxlen=0):

    if type(d) is Namespace:
        d = vars(d)

    for k in d:
        t   = type(d[k])
        if t is dict or t is Namespace:
            dlen    = rec_key_len(d[k], prefix_len+4, maxlen)
            maxlen  = dlen if dlen > maxlen else maxlen
        else:
            maxlen  = len(k) + prefix_len if len(k) > maxlen else maxlen

    return maxlen


# recursive pretty printing of dictionaries and Namespaces
def rec_print(d, prefix='', maxlen=0, sep=' : ', sep_len=3):

    if d and type(d) is Namespace:
        d = vars(d)

    if d:
        maxlen  = rec_key_len(d, len(prefix), maxlen)
        for k in d:
            t   = type(d[k])
            if t is dict or t is Namespace:
                print(f"{prefix}{k} :\n")
                rec_print(d[k], prefix+'    ', maxlen)
            else:
                v = d[k] if type(d[k]) != str else f"\'{d[k]}\'"
                print(f"{prefix}{k}{sep}{' '*(maxlen+sep_len-len(k)-len(prefix))}{v}")
        print()


# identical in call signature to ArgumentParser
# create needed dictionaries and lists, call super
class ArgParseDirector(ArgumentParser):
    def __init__(self, *args, **kwargs):


        # must create the dictionary add_argument uses here, because super calls add_argument()
        self.__def_dict = {}
        super(ArgParseDirector, self).__init__(*args, **kwargs)

        # merg_args() populates these in from the config file
        self.__config_args_d    = {}            # dictionary of configuration args
        self.__config_grps_d    = {}            # dictionary of group lists
        self.__config_rqrd_d    = {}            # dictionary of required/positional args

        # add_argument() tracks group names and required arguments in these
        self.__group_names_l    = []            # list of group names
        self.__reqrd_args_d     = {}            # list of required command line args

        # store the config file name if used - only so user can get it with get_config_file_name()
        self.__config_file_name = None


    # superset of ArgumentParser.add_argument(), accepts argument arg_group - create/add to arg group
    def add_argument(self, *args, default=None, arg_group=None, **kwargs):

        # for each arg
        #   if positional
        #       save arg and type
        #   else
        #       get default and process with type func if available, save in __def_dict
        #       if arg_group present: create inst var and save group name if not already done
        #       add arg to inst var
        for a in args:
            if a!='--help' and a!='-h':

                argtype = kwargs.get('type', None)
                if not self._has_prefix(a):
                    self.__reqrd_args_d[a]   = argtype

                else:
                    # actions 'store_true' and 'store_false' have default defaults - enforce here, as setting to None breaks them
                    if kwargs.get('action', None)=='store_true':
                        default     = False
                    elif kwargs.get('action', None)=='store_false':
                        default     = True

                    v       = default if argtype is None else argtype(default) if default is not None else None
                    self.__def_dict[self._remove_prefix(a)]  = v 

                    # if arg_group
                    #   if tuple
                    #       for each entry
                    #           create inst var if needed, add name to names list
                    #   else
                    #       create inst var if needed, add name to names list
                    if arg_group is not None:
                        if type(arg_group) is tuple:
                            for g in arg_group:
                                if not hasattr(self, g):
                                    self.__dict__[g]    = []
                                    self.__group_names_l.append(g)

                                self.__dict__[g].append(self._remove_prefix(a))
                        else:
                            if not hasattr(self, arg_group):
                                self.__dict__[arg_group]    = []
                                self.__group_names_l.append(arg_group)

                            self.__dict__[arg_group].append(self._remove_prefix(a))

        # let argparse do the rest
        super().add_argument(*args, default=None if a!='--help' and a!='-h' else default, **kwargs)


    # parse arguments -- 
    # get config file if it exists
    #   exec() it, get dictionaries
    # if required_args, manipulate command line to put things in place for super
    # remove --config_path from command line
    # merge config dictionaries and returned unaltered Namespace from super()
    def parse_args(self, *args, config_path=None, **kwargs):

        # need config_path BEFORE we call super parse.args to get required positional arguments - go directly into sys.argv
        # try to get --config_path from command line
        #  if there but ill formed exit
        #  if not there, use config_path
        config_name             = config_path
        idx                     = 0
        try:
            idx     = sys.argv.index('--config_path')
        except ValueError:
            # config_path not on command line
            pass

        # idx will index --config_path if it was found ...
        # if --config_path found
        #   if argv holds at least one more item
        #       get it
        #       if it doesn't name an exiting file, exit
        #       set config_name to the file
        #   else no value for --config_path, exit
        if idx>0:
            if len(sys.argv)>idx+1:
                fname   = sys.argv[idx+1]
                if not os.path.exists(fname):
                    exit(f"config_path {fname} does not exist - exiting()")

                config_name         = fname
            else:
                exit(f"config_path file name not specified - exiting()")

        # open file, read int str, add code at bottom to move dictionaries to locals()
        # exec() str, get dictionaries for configured args, groups, required/positional args
        if config_name is not None:

            # save file name
            self.__config_file_name = config_name

            with open(config_name, 'r') as config_file:
                config_str          = config_file.read()

            config_str             +=  "\nlocals()['config_args_d']=config_args     if 'config_groups' in locals() else {}\n" +\
                                         "locals()['config_grps_d']=config_groups   if 'config_groups' in locals() else {}\n" +\
                                         "locals()['config_rqrd_d']=config_required if 'config_required' in locals() else {}\n"

            exec(config_str, globals(), locals())
            self.__config_args_d    = locals()['config_args_d']
            self.__config_grps_d    = locals()['config_grps_d']
            self.__config_rqrd_d    = locals()['config_rqrd_d']


        # required args are positional and MUST be inserted into sys.argv
        # for each key in positional args set with add_argument()
        #   if at end of cmdline or within and not --config_path
        #       if config_rqrd_d has any entries
        #           if entry is a list, add each item from list to sys.argv one at a time
        #           else insert value from config_required/self.__config_rgrd_d
        j = 1
        for k in self.__reqrd_args_d:
            if j==len(sys.argv) or sys.argv[j]=='--config_path':
                if len(self.__config_rqrd_d)>0:
                    if type(self.__config_rqrd_d[k]) == list:
                        for e in self.__config_rqrd_d[k]:
                            v  = e if type(e)==str else f"{e}"
                            sys.argv.insert(j, v)
                            j += 1
                    else:
                        v               = self.__config_rqrd_d[k] if type(self.__config_rqrd_d[k])==str else f"{self.__config_rqrd_d[k]}"
                        sys.argv.insert(j, v)
                        j     += 1
            else:
                j         += 1

        # find --config_path if it exists and remove it and file name from cmd line
        # NOTE: if code gets here '--config_path' either isn't present or is well formed
        try:
            idx     = sys.argv.index('--config_path')
            del sys.argv[idx+1]
            del sys.argv[idx]
        except ValueError:
            pass

        # get super to do all the hard work, merge args dictionary with config dicitionaries, convert to Namespace, and return it
        args_d                      = vars(super().parse_args(*args, **kwargs))
        merged_args                 = self.merge_args(args_d)
        return merged_args


    # merge argument dictionary with config file and command line
    # NOTE: positional args were processed by super().parse_args()
    def merge_args(self, args_d):

        # process group names from configuration file, creating inst vars and adding to names as needed
        for g in self.__config_grps_d:
            if not hasattr(self, g):
                self.__dict__[g]    = []
                self.__group_names_l.append(g)

            for k in self.__config_grps_d[g]:
                if k not in self.__dict__[g]:
                    self.__dict__[g].append(k)

        # create new_args dict, if any __group names, create name dict as entry in new_args
        new_args        = {}
        for g in self.__group_names_l:
            new_args[g] = {}

        # create set of keys, combining args_d, config_d:
        keyset      = set()
        if args_d is not None:
            for k in args_d:
                keyset.add(k)

        for k in self.__config_args_d:
            keyset.add(k)

        # set v: cmdline 1st, config 2nd, default 3rd:
        for k in keyset:

            v   = None
            if args_d     and k in args_d and args_d[k] is not None:
                v   = args_d[k]
            # elif self.__config_args_d and k in self.__config_args_d:
            elif k in self.__config_args_d:
                v   = self.__config_args_d[k]
            # elif self.__def_dict and k in self.__def_dict:
            elif k in self.__def_dict:
                v   = self.__def_dict[k]

            # add v to new_args, and if in a group, to the group
            # for each group in __group_names
            #   if k in list, add to __group, else to new_args
            new_args[k]         = v
            for g in self.__group_names_l:
                if k in self.__dict__[g]:
                    new_args[g][k]  = v

        # convert __group_names to Namespaces
        for g in self.__group_names_l:
            new_args[g]             = Namespace(**new_args[g]) 

        # return new_args Namepsace
        return Namespace(**new_args)


    # generates a config file
    # generates a valid configuration file named by argument fname
    # will contain all arguments added with add_argument(). those with group names will also be added to group lists.
    def gen_config_file(self , fname, prefix='    ', tablen=4):

        # if anything in the default dictionary built be add_argument()
        #   if fname exists, warn user
        #   process dictionaries 
        if len(self.__def_dict) > 0:
            if os.path.exists(fname):
                if input(f"\t{fname} exists: replace? [y/n]: ")!='y':
                    print(f'exiting: please rename \'{fname}\' or change target config file name')

            # get longest key so config file can be easy to read
            # open file
            #   write preamble and entries for each dictionary
            maxlen                  = rec_key_len(self.__def_dict, len(prefix)) + 4     # len of key string
            keylen                  = maxlen+4                                          # maxlen + len of quotes, colon, and 1 trailing space
            keylen                  = keylen if keylen%tablen==0 else keylen+(tablen-(keylen%tablen))
            with open(fname, 'w') as config_file:
                config_file.write(f"# ArgParseDirector configuration file '{fname}': original generated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                config_file.write(f"# '{fname}' may be edited to:\n#\tadd/change entries and values in config_args,\n#\tadd/change group names and keys in config_groups,\n#\tchange values for positional args in config_required\n#\tor add python code as needed")

                config_file.write(f"\n\n# config_args: original generated from all args added with add_argument()\n")
                config_file.write(f"# change values to override defaults, add keys to create arguments that will be returned from parse_args() but not available from command line\n")
                config_file.write("# do not change dictionary name 'config_args'\n")
                config_file.write("config_args = {\n")

                # generate history prolog
                config_file.write(f"{prefix}\'{'net_history'}\': {' '*(keylen-len('net_history')-len(prefix))}\'\',\n")
                config_file.write(f"{prefix}\'{'net_desc'}\': {' '*(keylen-len('net_desc')-len(prefix))}\'00:  \\n\',\n\n")
                
                for k in self.__def_dict:
                    v               = f"\'{self.__def_dict[k]}\'" if type(self.__def_dict[k])==str else None if type(self.__def_dict[k]) is type(None) else self.__def_dict[k]
                    config_file.write(f"{prefix}\'{k}\': {' '*(keylen-len(k)-len(prefix))}{v},\n")
                config_file.write("}\n")

                config_file.write(f"\n# config_groups: from all args added with add_argument() call that includes 'arg_group = 'some_group_name' or ('group1', 'group2')\n")
                config_file.write(f"# add names to lists, or create new groups\n")
                config_file.write("# do not change dictionary name 'config_groups'\n")
                config_file.write("config_groups = {\n")
                for k in self.__group_names_l:
                    config_file.write(f"{prefix}\'{k}\': [\n")
                    for n in self.__dict__[k]:
                        config_file.write(f"{prefix*2}\'{n}\',\n")
                    config_file.write(f"{prefix}],\n")
                config_file.write("}\n")

                config_file.write("\n# required arguments: from all args added as positional with add_argument()\n")
                config_file.write("# change values, do NOT remove or add any entries\n")
                config_file.write("# do not change dictionary name 'config_required'\n")
                config_file.write("config_required = {\n")
                for k in self.__reqrd_args_d:
                    config_file.write(f"{prefix}\'{k}\': {' '*(keylen-len(k)-len(prefix))}'{self.__reqrd_args_d[k]} VALUE NEEDED HERE',\n")
                config_file.write("}\n")


    # return full path and name of config file if one was used
    def get_config_file_name(self):
        return self.__config_file_name

    # test if arg has a prefix: no prefix signals required option
    def _has_prefix(self, arg):
        return re.match(f'[{self.prefix_chars}]', arg) is not None

    # remove any prefix characeters from arg
    def _remove_prefix(self, arg):
        return re.sub(f'[{self.prefix_chars}]', '', arg)

