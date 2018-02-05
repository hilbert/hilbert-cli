"""
This is a modified version of https://github.com/druths/arghandler/blob/master/arghandler/base.py
by Derek Ruths, which is available under Apache License, Version 2.0
"""

# import arghandler                      # NOQA

import argparse  # NOQA
import inspect  # NOQA
import logging  # NOQA
from operator import attrgetter

log = logging.getLogger(__name__)  #

#################################
# decorator
#################################
registered_subcommands = {}
registered_subcommands_help = {}


def subcmd(arg=None, **kwargs):
    """
    This decorator is used to register functions as subcommands with instances
    of SubCommandHandler.
    """
    if inspect.isfunction(arg):
        return subcmd_fxn(arg, arg.__name__, kwargs)
    else:
        def inner_subcmd(fxn):
            return subcmd_fxn(fxn, arg, kwargs)

        return inner_subcmd


def subcmd_fxn(cmd_fxn, name, kwargs):
    global registered_subcommands, registered_subcommands_help

    # get the name of the command
    if name is None:
        name = cmd_fxn.__name__

    if (name in registered_subcommands) or (name in registered_subcommands_help):
        raise Exception("Duplicated sub-command [{0}]! Old handler: [{1}], new one: [{2}]".format(name, registered_subcommands[name].__name__, cmd_fxn.__name__))

    registered_subcommands[name] = cmd_fxn
    registered_subcommands_help[name] = kwargs.pop('help', '')

    return cmd_fxn


#########################
class SortingHelpFormatter(argparse.RawTextHelpFormatter):
    def __init__(self, *args, **kwargs):
        kwargs['indent_increment'] = 1
        kwargs['max_help_position'] = 17
        super(SortingHelpFormatter, self).__init__(*args, **kwargs)


#########################
class SubCommandHandler(argparse.ArgumentParser):
    """Modified ArgumentHandler from https://github.com/druths/arghandler"""

    def __init__(self, *args, **kwargs):
        """
        All constructor arguments are the same as found in `argparse.ArgumentParser`.

        kwargs
        ------
          * `use_subcommand_help [=False]`: when printing out the help message, use a shortened
            version of the help message that simply shows the sub-commands supported and
            their description.

          * `enable_autocompletion [=False]`: make it so that the command line
            supports autocompletion

        """

        ### extract any special keywords here
        self._use_subcommand_help = kwargs.pop('use_subcommand_help', False)
        self._enable_autocompletion = kwargs.pop('enable_autocompletion', False)

        self._ignore_remainder = False
        self._use_subcommands = True
        self._subcommand_lookup = dict()
        self._subcommand_help = dict()

        self._has_parsed = False

        # setup the class
        if self._use_subcommand_help:
            kwargs['formatter_class'] = SortingHelpFormatter

        super(SubCommandHandler, self).__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        """
        This has the same functionality as `argparse.ArgumentParser.add_argument`.
        """
        # just watch for the REMAINDER nargs to see if subcommands are relevant

        assert not (self._ignore_remainder and 'nargs' in kwargs and kwargs['nargs'] == argparse.REMAINDER)
        #    self._use_subcommands = False

        return super(SubCommandHandler, self).add_argument(*args, **kwargs)

    def set_subcommands(self, subcommand_lookup):
        """
        Provide a set of subcommands that this instance of ArgumentHandler should
        support.  This is an alternative to using the decorator `@subcmd`. Note that
        the total set of subcommands supported will be those specified in this method
        combined with those identified by the decorator.
        """
        if type(subcommand_lookup) is not dict:
            raise TypeError('subcommands must be specified as a dict')

        # sanity check the subcommands
        self._subcommand_lookup = {}
        self._subcommand_help = {}
        for cn, cf in subcommand_lookup.items():
            if type(cn) is not str:
                raise TypeError('subcommand keys must be strings. Found %s' % str(cn))
            if type(cf) == tuple:
                if not callable(cf[0]):
                    raise TypeError('subcommand with name %s must be callable' % cn)
                else:
                    self._subcommand_lookup[cn] = cf[0]
                    self._subcommand_help[cn] = cf[1]
            elif not callable(cf):
                raise TypeError('subcommand with name %s must be callable' % cn)
            else:
                self._subcommand_lookup[cn] = cf
                self._subcommand_help[cn] = ''

        return

    def parse_args(self, argv=None):
        """
        Works the same as `argparse.ArgumentParser.parse_args`.
        """
        group = self.add_mutually_exclusive_group()
        group.add_argument("-v", "--verbose", action=CountedVerboseAction, help='increase verbosity')
        group.add_argument("-q", "--quiet", action=CountedQuietAction, help='decrease verbosity')

        # add_argument, set_logging_level, set_subcommands,
        #    handler.set_logging_argument('-l', '--log_level', default_level=logging.INFO)

        self.add_argument('-H', '--helpall', action=HelpAllAction,
                          nargs=0, default=argparse.SUPPRESS, required=False, type=None, metavar=None,
                          help="show detailed help and exit")

        global registered_subcommands, registered_subcommands_help

        if self._has_parsed:
            raise Exception('ArgumentHandler.parse_args can only be called once')

        # collect subcommands into _subcommand_lookup
        for cn, cf in registered_subcommands.items():
            self._subcommand_lookup[cn] = cf
            self._subcommand_help[cn] = registered_subcommands_help[cn]

        assert len(self._subcommand_lookup) > 0
        #            self._use_subcommands = False

        # add in subcommands if appropriate
        assert self._use_subcommands
        #        if not self._use_subcommands:
        #            pass
        #        else:
        max_cmd_length = max([len(x) for x in self._subcommand_lookup.keys()])
        subcommands_help_text = 'the subcommand to run'
        if self._use_subcommand_help:
            subcommands_help_text = ':\n'
            for command in sorted(self._subcommand_lookup.keys()):  # Sorted...
                subcommands_help_text += command.ljust(max_cmd_length + 2)
                subcommands_help_text += self._subcommand_help[command]
                subcommands_help_text += '\n'

        self.add_argument('cmd', choices=self._subcommand_lookup.keys(), help=subcommands_help_text,
                          metavar='subcommand')

        cargs_help_msg = 'arguments for the subcommand' if not self._use_subcommand_help else argparse.SUPPRESS
        self.add_argument('cargs', nargs=argparse.REMAINDER, help=cargs_help_msg)

        # handle autocompletion if requested
        if self._enable_autocompletion:
            import argcomplete
            argcomplete.autocomplete(self)

        # parse arguments
        args = super(SubCommandHandler, self).parse_args(argv)

        self._has_parse = True

        #        cargs_help_msg = 'arguments for the subcommand' if not self._use_subcommand_help else argparse.SUPPRESS
        #        self.add_argument('cargs', nargs=argparse.REMAINDER, help=cargs_help_msg)

        return args

    def run(self, argv=None, context_fxn=None):
        """
        This method triggers a three step process:

          1) Parse the arguments in `argv`. If not specified, `sys.argv` is
             used.

          2) Configure the logging level.  This only happens if the
             `set_logging_argument` was called.

          3) Run the appropriate subcommand.  This only happens if subcommands
             are available and enabled. Prior to the subcommand being run,
             the `context_fxn` is called.  This function accepts one argument -
             the namespace returned by a call to `parse_args`.

        The parsed arguments are all returned.
        """
        # get the arguments
        args = self.parse_args(argv)

        # # handle the logging argument
        # if self._logging_argument:
        #     level = eval('args.%s' % self._logging_argument)
        #
        #     # convert the level
        #     level = eval('logging.%s' % level)
        #
        #     # call the logging config fxn
        #     self._logging_config_fxn(level, args)

        #        self.logging_handler(args)
        #        pedantic_handler(self, vars(args))

        # generate the context
        context = args
        if context_fxn:
            context = context_fxn(args)

        # create the sub command argument parser
        scmd_parser = argparse.ArgumentParser(prog='%s %s' % (self.prog, args.cmd), add_help=True)

        # handle the subcommands
        self._subcommand_lookup[args.cmd](scmd_parser, context, args.cargs)

        return args  # run()


# logging.CRITICAL = 50
# logging.ERROR = 40
# logging.WARNING = 30
# logging.INFO = 20
# logging.DEBUG = 10
# logging.NOTSET = 0
class CountedVerboseAction(argparse._CountAction):
    def __init__(self, *args, **kwargs):
        super(CountedVerboseAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        new_count = argparse._ensure_value(namespace, self.dest, 0) + 1
        setattr(namespace, self.dest, new_count)

        _log = logging.getLogger()  # root logger!
        level = max(logging.DEBUG, _log.level - logging.DEBUG)

        if _log.level != level:
            log.debug("Changing logging level: %s -> %s",
                      logging.getLevelName(_log.level),
                      logging.getLevelName(level))
            _log.setLevel(level)
            log.debug("New logging level: %s", logging.getLevelName(_log.level))


class CountedQuietAction(argparse._CountAction):
    def __init__(self, *args, **kwargs):
        super(CountedQuietAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        new_count = argparse._ensure_value(namespace, self.dest, 0) + 1
        setattr(namespace, self.dest, new_count)

        _log = logging.getLogger()  # root logger!
        level = min(logging.CRITICAL, _log.level + logging.DEBUG)

        if _log.level != level:
            log.debug("Changing logging level: %s -> %s",
                      logging.getLevelName(_log.level),
                      logging.getLevelName(level))
            _log.setLevel(level)
            log.debug("New logging level: %s", logging.getLevelName(_log.level))


class MyHelpAction(argparse.Action):  ### _HelpAction??
    def __init__(self,
                 option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None):
        super(MyHelpAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        raise BaseException("Help was printed!")


class HelpAllAction(argparse.Action):  ### _HelpAction??
    def __init__(self, option_strings, *args, **kwargs):
        super(HelpAllAction, self).__init__(option_strings=option_strings, *args, **kwargs)

    def __call__(self, parser, args, values, option_string=None):
        for cn in sorted(parser._subcommand_lookup.keys()):
            # create the sub command argument parser
            scmd_parser = argparse.ArgumentParser(prog='%s %s' % (parser.prog, cn), add_help=False)
            scmd_parser.add_argument('-h', '--help', action=MyHelpAction, help="show %(prog)s's help message")
            try:
                print('\n')
                a = parser._subcommand_lookup[cn](scmd_parser, args, ['--help'])
            except:
                pass

        parser.exit()
        setattr(args, self.dest, values)
