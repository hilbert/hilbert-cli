# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

###############################################################
import ruamel.yaml as yaml
from ruamel.yaml.reader import Reader
from ruamel.yaml.scanner import RoundTripScanner  # Scanner
from ruamel.yaml.parser import RoundTripParser  # Parser,
from ruamel.yaml.composer import Composer
from ruamel.yaml.constructor import RoundTripConstructor  # Constructor, SafeConstructor,
from ruamel.yaml.resolver import VersionedResolver  # Resolver,
# from ruamel.yaml.nodes import MappingNode
from ruamel.yaml.compat import PY2, PY3, text_type, string_types, ordereddict

import semantic_version  # supports partial versions

import logging
import collections
import sys
import os
import re, tokenize
import tempfile
import subprocess, shlex
# import paramiko


import pprint as PP
from abc import *

###############################################################
logging.basicConfig(format='%(levelname)s  [%(filename)s:%(lineno)d]: %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

_pp = PP.PrettyPrinter(indent=4)

###############################################################
# NOTE: Global variables
PEDANTIC = False  # NOTE: to treat invalid values/keys as errors?
INPUT_DIRNAME = './'  # NOTE: base location for external resources


###############################################################
if PY3 and (sys.version_info[1] >= 4):
    class AbstractValidator(ABC):
        """AbstractValidator is the root Base class for any concrete implementation of entities
        appearing in the general configuration file"""

        @abstractmethod
        def validate(self, d):
            pass
elif PY2 or PY3:
    class AbstractValidator:
        """AbstractValidator is the root Base class for any concrete implementation of entities
        appearing in the general configuration file"""
        __metaclass__ = ABCMeta

        @abstractmethod
        def validate(self, d):
            pass
# elif PY3:
#    class AbstractValidator(metaclass=ABCMeta):
#        """AbstractValidator is the root Base class for any concrete implementation of entities
#        appearing in the general configuration file"""
#        @abstractmethod
#        def validate(self, d):
#            pass
else:
    raise NotImplementedError("Unsupported Python version: '{}'".format(sys.version_info))

###############################################################
if PY3:
    from urllib.parse import urlparse
    from urllib.request import urlopen
elif PY2:
    from urlparse import urlparse
    from urllib2 import urlopen

###############################################################
if PY3:
    def is_valid_id(k):
        return k.isidentifier()
elif PY2:
    def is_valid_id(k):
        return re.match(tokenize.Name + '$', k)


###############################################################
def pprint(cfg):
    global _pp
    _pp.pprint(cfg)


###############################################################
def _execute(_cmd, timeout=None, shell=False, stdout=None, stderr=None):  # True??? Try several times? Overall timeout?
    global PEDANTIC
    __cmd = ' '.join(_cmd)
    # stdout = tmp, stderr = open("/dev/null", 'w')
    # stdout=open("/dev/null", 'w'), stderr=open("/dev/null", 'w'))
    log.debug("Executing shell command: '{}'...".format(__cmd))

    retcode = None
    with subprocess.Popen(_cmd, shell=shell, stdout=stdout, stderr=stderr) as p:
        try:
            retcode = p.wait(timeout=timeout)  # ?
        except:
            p.kill()
            p.wait()
            log.exception("Could not execute '{0}'! Exception: {1}".format(__cmd, sys.exc_info()))
            raise

    assert retcode is not None
    log.debug("Exit code: '{}'".format(retcode))

    if retcode:
        if not PEDANTIC:  # Bad error code [{0}] while
            log.warning("Error exit code {0}, while executing '{1}'!".format(retcode, __cmd))
        else:  # Pedantic mode?
            log.error("Error exit code {0}, while executing '{1}'!".format(retcode, __cmd))
            raise Exception("Error exit code {0}, while executing '{1}'".format(retcode, __cmd))
    else:
        log.debug("Successful command '{}' execution!".format(__cmd))

    return retcode


###############################################################
def _get_line_col(lc):

    if isinstance(lc, (list, tuple)):
        l = lc[0]
        c = lc[1]
    else:
        try:
            l = lc.line
        except:
            log.exception("Cannot get line out of '{}': Missing .line attribute!".format(lc))
            raise

        try:
            c = lc.col
        except:
            try:
                c = lc.column
            except:
                log.exception("Cannot get column out of '{}': Missing .col/.column attributes!".format(lc))
                raise

    return l, c


###############################################################
class ConfigurationError(Exception):
    def __init__(self, msg):
        self._msg = msg


###############################################################
_up_arrow = '↑'


def _key_error(key, value, lc, error_message, e='K'):
    (line, col) = _get_line_col(lc)

    if key is None:
        key = '*'

    print('{}[line: {}, column: {}]: {}'.format(e, line + 1, col + 1, error_message.format(key)))
    print('{}{}: {}'.format(' ' * col, key, value))  # NOTE: !?
    # ! TODO: try to get access to original ruamel.yaml buffered lines...?
    print('{}{}'.format(' ' * col, _up_arrow))
    print('---')


def _key_note(key, lc, key_message, e='K'):
    (line, col) = _get_line_col(lc)

    if key is None:
        key = '?'

    print('{}[line: {}, column: {}]: {}'.format(e, line + 1, col + 1, key_message.format(key)))
    print('---')


def _value_error(key, value, lc, error, e='E'):
    (line, col) = _get_line_col(lc)

    if key is None:
        key = '?'

    val_col = col + len(key) + 2
    print('{}[line: {}, column: {}]: {}'.format(e, line + 1, val_col + 1, error.format(key)))
    print('{}{}: {}'.format(' ' * col, key, value))  # NOTE: !?
    # ! TODO: try to get access to original ruamel.yaml buffered lines...?
    print('{}{}'.format(' ' * val_col, _up_arrow))
    print('---')

# Unused???
# def value_warning(key, value, lc, error):
#    _value_error(key, value, lc, error, e='W')


###############################################################
class VerboseRoundTripConstructor(RoundTripConstructor):
    def construct_mapping(self, node, maptyp, deep=False):

        m = RoundTripConstructor.construct_mapping(self, node, maptyp, deep=deep)  # the actual construction!

        # additionally go through all nodes in the mapping to detect overwrites:

        starts = {}  # already processed keys + locations and values

        for key_node, value_node in node.value:
            # keys can be list -> deep
            key = self.construct_object(key_node, deep=True)

            # lists are not hashable, but tuples are
            if not isinstance(key, collections.Hashable):
                if isinstance(key, list):
                    key = tuple(key)

            value = self.construct_object(value_node, deep=deep)
            # TODO: check the lines above in the original Constructor.construct_mapping code for any changes/updates

            if key in starts:  # Duplication detection
                old = starts[key]

                print("WARNING: Key re-definition within some mapping: ")  # mapping details?
                _key_error(key, old[1], old[0], "Previous Value: ")
                _key_error(key, value, key_node.start_mark, "New Value: ")
                print('===')

            starts[key] = (key_node.start_mark, value)  # in order to find all such problems!

        return m


###############################################################
class VerboseRoundTripLoader(Reader, RoundTripScanner, RoundTripParser, Composer,
                             VerboseRoundTripConstructor, VersionedResolver):
    def __init__(self, stream, version=None, preserve_quotes=None):
        Reader.__init__(self, stream)
        RoundTripScanner.__init__(self)
        RoundTripParser.__init__(self)
        Composer.__init__(self)
        VerboseRoundTripConstructor.__init__(self, preserve_quotes=preserve_quotes)
        VersionedResolver.__init__(self, version)


###############################################################
class BaseValidator(AbstractValidator):
    """Abstract Base Class for the Config entities"""

    __version = [None]    # NOTE: shared version among all Validator Classes!
    _parent   = None      # NOTE: (for later) parent Validator
    _data     = None      # NOTE: result of valid validation
    _default_input_data = None  # NOTE: Default input to the parser instead of None

    def __init__(self, *args, **kwargs):
        parent = kwargs.pop('parent', None)
        parsed_result_is_data = kwargs.pop('parsed_result_is_data', False)

        # TODO: FIXME: assure *args, **kwargs are empty!
        super(BaseValidator, self).__init__()

        assert self._parent is None
        self._parent = parent

        # parsed_result_is_data default:
        # - False => parsed result is self
        # - True => get_data()
        self._parsed_result_is_data = parsed_result_is_data

        self.__API_VERSION_ID = "$Id$"

    def get_parent(self, cls=None):
        if cls is None:
            return self._parent

        if self._parent is None:
            return None

        _p = self._parent
        while isinstance(_p, BaseValidator):
            if isinstance(_p, cls):
                break
            _t = _p._parent
            if _t is None:
                break
            _p = _t

        assert _p is not None
        if isinstance(_p, cls):
            return _p

        log.error("Sorry: could not find parent of specified class ({0})!"
                  "Found top is of type: {1}".format(cls, type(_p)))
        return None


    def get_api_version(self):
        return self.__API_VERSION_ID

    def set_data(self, d):
        # assert self._data is None
        # assert d is not None
        self._data = d

    def get_data(self):
        _d = self._data
#        assert _d is not None
        return _d

    @classmethod
    def set_version(cls, v):
        """To be set once only for any Validator class!"""
        assert len(cls.__version) == 1
#        assert cls.__version[0] is None  # NOTE: bad for testing!
        cls.__version[0] = v

    @classmethod
    def get_version(cls, default=None):
        assert len(cls.__version) == 1

        if cls.__version[0] is not None:
            return cls.__version[0]

        return default

    @abstractmethod
    def validate(self, d):  # abstract...
        pass

    @classmethod
    def parse(cls, d, *args, **kwargs):
        """
        return parsed value, throw exception if input is invalid!

        :param d:
        :param parent:
        :return:
        """
        self = cls(*args, **kwargs)

        log.debug("{1}::parse( input type: {0} )".format(type(d), type(self)))

        if self.validate(d):  # NOTE: validate should not **explicitly** throw exceptions!!!
            if self._parsed_result_is_data:
                return self.get_data()

            return self

        # NOTE: .parse should throw exceptions in case of invalid input data!
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data: '{0}' in {1}!" .format(d, type(self))))

    def __repr__(self):
        """Print using pretty formatter"""

        d = self.get_data()  # vars(self) # ???
        return PP.pformat(d, indent=4, width=100)

#    def __str__(self):
#        """Convert to string"""
#
#        d = self.get_data()  # vars(self) # ???
#        return str(d)

    def __eq__(self, other):
        assert isinstance(self, BaseValidator)

        if not isinstance(other, BaseValidator):
            return self.data_dump() == other

        assert isinstance(other, BaseValidator)

#        assert self.get_api_version() == other.get_api_version()
        return self.get_data() == other.get_data()

    def __ne__(self, other):
        return not (self == other)  # More general than self.value != other.value

    def data_dump(self):
        _d = self.get_data()

        if _d is None:
            return _d

        assert not isinstance(_d, (tuple, set))  # TODO: is this true in general?!?

        if isinstance(_d, dict):
            _dd = {}
            for k in _d:
                v = _d[k]
                if isinstance(v, BaseValidator):
                    v = v.data_dump()
                _dd[k] = v
            return _dd

        if isinstance(_d, list):
            _dd = []
            for idx, i in enumerate(_d):
                v = i
                if isinstance(v, BaseValidator):
                    v = v.data_dump()
                _dd.insert(idx,  v)
            return _dd

#        if isinstance(_d, string_types):
        return _d

    def query(self, what):
        """
        Generic query for data subset about this object

        A/B/C/(all|keys|data)?

        Get object under A/B/C and return
        * it (if 'all') - default!
        * its keys (if 'keys')
        * its data dump (if 'data')
        """

        # NOTE: no data dumping here! Result may be a validator!

        log.debug("Querying '%s'", what)

        if (what is None) or (what == ''):
            what = 'all'

        if what == 'all':
            return self

        if what == 'data':
            return self.data_dump()

        _d = self.get_data()

        if what == 'keys':
            assert isinstance(_d, dict)
            return [k for k in _d.keys()]

        s = StringValidator.parse(what, parent=self)

        if s in _d:
            return _d[s]

        sep = "/"
        ss = s.split(sep)  # NOTE: encode using pathes!

        h = ss[0]  # top header
        t = sep.join(ss[1:])  # tail

        if h in _d:
            d = _d[ss[0]]
            if isinstance(d, BaseValidator):
                return d.query(t)  # TODO: FIXME: avoid recursion...

            log.warning("Could not query an object. Ignoring the tail: %s", t)
            return d

        raise ConfigurationError(u"{}: {}".format("ERROR:",
                                                  "Sorry cannot show '{0}' of {1}!".format(what, type(self))))


###############################################################
class BaseRecordValidator(BaseValidator):
    """Aggregation of data as a record with some fixed data members"""

    # TODO: turn _default_type into a class-member (by moving it here)...?

    def __init__(self, *args, **kwargs):
        super(BaseRecordValidator, self).__init__(*args, **kwargs)

        self._default_type = None  # "default_base"
        self._types = {}
        self._create_optional = False  # Instantiate missing optional keys
        self._type = None

    def detect_type(self, d):
        """determine the type of variadic data for the format version"""

        assert not (self._default_type is None)
        assert len(self._types) > 0
        assert isinstance(d, dict)

        return self._default_type

    def detect_extra_rule(self, key, value):
        """Handling for extra un-recorded keys in the mapping"""
        return None

    def validate(self, d):
        if d is None:
            d = self._default_input_data

        # ! TODO: assert that d is a mapping with lc!

        self._type = self.detect_type(d)

        assert self._type is not None
        assert self._type in self._types

        _rule = self._types[self._type]

        _ret = True

        _d = {}
        _lc = d.lc  # starting location of the mapping...?

        for k in _rule.keys():
            r = _rule[k]
            if r[0] and (k not in d):
                _key_note(k, _lc, "ERROR: Missing mandatory key `{}` (type: '%s')" % (self._type))  # Raise Exception?
                _ret = False
            # NOTE: the following will add all the missing default values
            elif self._create_optional and (not r[0]):  # Optional Values should have some default values!
                # TODO: FIXME: catch exception in the following:
                _k = None
                _v = None
                try:
                    _k = StringValidator.parse(k, parent=self)
                except ConfigurationError as err:
                    _key_note(k, _lc, "Error: invalid _optional_ key field '{}' (type: '%s')" % self._type)
                    pprint(err)
                    _ret = False

                try:
                    _v = (r[1]).parse(None, parent=self)  # Default Value!
                except ConfigurationError as err:
                    _key_note(k, _lc, "Error: invalid default value (for optional key: '{}') (type: '%s')" % self._type)
                    pprint(err)
                    _ret = False

                if _ret:
                    assert _k is not None
                    _d[_k] = _v

        (s, c) = _get_line_col(_lc)
        for offset, k in enumerate(d):
            v = d.get(k)
            k = text_type(k)
            l = s + offset  # ??
            lc = (l, c)

            _k = None
            _v = None

            if k in _rule:
                try:
                    _k = StringValidator.parse(k, parent=self)
                except ConfigurationError as err:
                    _key_error(k, v, lc, "Error: invalid key field '{}' (type: '%s')" % self._type)
                    pprint(err)
                    _ret = False

                try:
                    _v = (_rule[k][1]).parse(v, parent=self)
                except ConfigurationError as err:
                    _value_error(k, v, lc, "Error: invalid field value (key: '{}') (type: '%s')" % self._type)
                    pprint(err)
                    _ret = False

            else:
                _extra_rule = self.detect_extra_rule(k, v)  # (KeyValidator, ValueValidator)

                if _extra_rule is None:
                    _key_error(k, v, lc, "WARNING: Unhandled extra Key: '{}' (type: '%s')" % self._type)
                    _ret = False
                else:
                    try:
                        _k = (_extra_rule[0]).parse(k, parent=self)
                    except ConfigurationError as err:
                        _key_error(k, v, lc, "Error: invalid key '{}' (type: '%s')" % self._type)
                        pprint(err)
                        _ret = False

                    try:
                        _v = (_extra_rule[1]).parse(v, parent=self)
                    except ConfigurationError as err:
                        # TODO: FIXME: wrong col (it was for key - not value)!
                        _value_error(k, v, lc, "Error: invalid field value '{}' value (type: '%s')" % self._type)
                        pprint(err)
                        _ret = False

            if _ret:
                assert _k is not None
                _d[_k] = _v

        if _ret:
            self.set_data(_d)

        return _ret


###############################################################
class ScalarValidator(BaseValidator):
    """Single scalar value out of YAML scalars: strings, numbert etc."""

    def __init__(self, *args, **kwargs):
        kwargs['parsed_result_is_data'] = kwargs.pop('parsed_result_is_data', True)
        super(ScalarValidator, self).__init__(*args, **kwargs)

    def validate(self, d):
        """check that data is a scalar: not a sequence or mapping or set"""

        if d is None:
            d = self._default_input_data  # !

        if d is not None:
            if isinstance(d, (list, dict, tuple, set)):  # ! Check if data is not a container?
                log.error("value: '{}' is not a scalar value!!" . format(d))
                return False

            if isinstance(d, string_types):
                d = text_type(d)

        # NOTE: None is also a scalar value...!
        self.set_data(d)
        return True

###############################################################
class StringValidator(ScalarValidator):
    """YAML String"""
    def __init__(self, *args, **kwargs):
        super(StringValidator, self).__init__(*args, **kwargs)

        self._default_input_data = ''

    def validate(self, d):
        """check whether data is a valid string. Note: should not care about format version"""

        if d is None:
            d = self._default_input_data

        assert d is not None

        s = ScalarValidator.parse(d, parent=self)

        if not isinstance(s, string_types):
            log.error("value: '{}' is not a string!!" . format(d))
            return False

        self.set_data(text_type(d))
        return True


###############################################################
class SemanticVersionValidator(BaseValidator):
    def __init__(self, *args, **kwargs):
        partial = kwargs.pop('partial', True)
#        kwargs['parsed_result_is_data'] = kwargs.pop('parsed_result_is_data', False)
        super(SemanticVersionValidator, self).__init__(*args, **kwargs)

#        self._parsed_result_is_data = False
        self._partial = partial
        self._default_input_data = '0.0.0'

    def validate(self, d):
        """check the string data to be a valid semantic version"""

        if d is None:
            d = self._default_input_data

        log.debug("{1}::validate( input type: {0} )".format(type(d), type(self)))
#        log.debug("SemanticVersionValidator::validate( input data: {0} )".format(str(d)))

        try:
            _t = StringValidator.parse(d, parent=self, parsed_result_is_data=True)
        except:
            log.warning("Input is not a string: {}".format(d))
            try:
                _t = StringValidator.parse(str(d), parent=self, parsed_result_is_data=True)
            except:
                log.error("Input cannot be converted into a version string: {}".format(d))
                return False


        # self.get_version(None) # ???
        _v = None
        try:
            _v = semantic_version.Version(_t, partial=self._partial)
        except:
            log.exception("Wrong version data: '{0}' (see: '{1}')" . format(d, sys.exc_info()))
            return False

        self.set_data(_v)
        return True

    def data_dump(self):
        return str(self.get_data())


###############################################################
class BaseUIString(StringValidator):
    """String visible to users => non empty!"""

    def __init__(self, *args, **kwargs):
        super(BaseUIString, self).__init__(*args, **kwargs)

        self._default_input_data = None

    def validate(self, d):
        """check whether data is a valid (non-empty) string"""

        if d is None:
            d = self._default_input_data

        if not super(BaseUIString, self).validate(d):
            self.set_data(None)
            return False

        if bool(self.get_data()):  # NOTE: Displayed string should not be empty!
            return True

        self.set_data(None)
        return False


###############################################################
class BaseEnum(BaseValidator):  # TODO: Generalize to not only strings...?
    """Enumeration/collection of several fixed strings"""

    def __init__(self, *args, **kwargs):
        kwargs['parsed_result_is_data'] = kwargs.pop('parsed_result_is_data', True)
        super(BaseEnum, self).__init__(*args, **kwargs)

        self._enum_list = []  # NOTE: will depend on the version...

    def validate(self, d):
        """check whether data is in the list of fixed strings (see ._enum_list)"""

        if d is None:
            d = self._default_input_data

        t = StringValidator.parse(d, parent=self, parsed_result_is_data=True)

        if not (t in self._enum_list): # check withing a list of possible string values
            log.error("string value: '{}' is not among known enum items!!".format(d))
            return False

        self.set_data(t)
        return True


###############################################################
class ServiceType(BaseEnum):  # Q: Is 'Service::type' mandatory? default: 'compose'
    def __init__(self, *args, **kwargs):
        super(ServiceType, self).__init__(*args, **kwargs)

        compose = text_type('compose')
        self._enum_list = [compose]  # NOTE: 'docker' and others may be possible later on
        self._default_input_data = compose


###############################################################
class StationOMDTag(BaseEnum):  # Q: Is 'Station::omd_tag' mandatory? default: 'standalone'
    def __init__(self, *args, **kwargs):
        super(StationOMDTag, self).__init__(*args, **kwargs)

        _v = text_type('standalone')
        self._enum_list = [text_type('agent'), text_type('windows'), _v]  # NOTE: possible values of omd_tag
        self._default_input_data = _v


###############################################################
class StationPowerOnMethodType(BaseEnum):  # Enum: [WOL], AMTvPRO, DockerMachine

    def __init__(self, *args, **kwargs):
        super(StationPowerOnMethodType, self).__init__(*args, **kwargs)

        wol = text_type('WOL')
        # NOTE: the list of possible values of PowerOnMethod::type (will depend on format version)
        self._enum_list = [wol, text_type('DockerMachine')]  # NOTE: 'AMTvPRO' and others may be possible later on
        self._default_input_data = wol


###############################################################
class URI(BaseValidator):
    """Location of external file, either URL or local absolute or local relative to the input config file"""

    def __init__(self, *args, **kwargs):
        kwargs['parsed_result_is_data'] = kwargs.pop('parsed_result_is_data', True)
        super(URI, self).__init__(*args, **kwargs)

        self._type = None

    def validate(self, d):
        """check whether data is a valid URI"""
        global PEDANTIC

        if d is None:
            d = self._default_input_data

        v = StringValidator.parse(d, parent=self, parsed_result_is_data=True)

        _ret = True

        # TODO: @classmethod def check_uri(v)
        if urlparse(v).scheme != '':
            self._type = text_type('url')
            try:
                urlopen(v).close()
            except:
                log.warning("URL: '{}' is not accessible!".format(v))
                _ret = not PEDANTIC

        # TODO: FIXME: base location should be the input file's dirname???
#        elif not os.path.isabs(v):
#            v = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), v))

        elif os.path.isfile(v):  # Check whether file exists
            self._type = text_type('file')

        elif os.path.isdir(v):  # Check whether directory exists
            self._type = text_type('dir')

        if not _ret:
            log.warning("missing/unsupported resource location: {}".format(v))
            _ret = (not PEDANTIC)

        if _ret:
            self.set_data(v)

        return _ret


###############################################################
class BaseID(BaseValidator):
    def __init__(self, *args, **kwargs):
        kwargs['parsed_result_is_data'] = kwargs.pop('parsed_result_is_data', True)
        super(BaseID, self).__init__(*args, **kwargs)

    def validate(self, d):
        """check whether data is a valid ID string"""

        if d is None:
            d = self._default_input_data

        v = StringValidator.parse(d, parent=self, parsed_result_is_data=True)

        if not is_valid_id(v):
            log.error("not a valid variable identifier! Input: '{}'" . format(d))
            return False

        self.set_data(v)
        return True

###############################################################
class ClientVariable(BaseID):  #
    def __init__(self, *args, **kwargs):
        super(ClientVariable, self).__init__(*args, **kwargs)

    def validate(self, d):
        """check whether data is a valid ID string"""

        if d is None:
            d = self._default_input_data

        v = BaseID.parse(d, parent=self)  # .get_data()

        _ret = True

        if not (v == v.lower() or v == v.upper()):  # ! Variables are all lower or upper case!
            log.error("a variable must be either in lower or upper case! Input: '{}'" . format(d))
            _ret = False

        # NOTE: starting with hilbert_ or HILBERT_ with letters, digits and '_'??
        if not re.match('^hilbert(_[a-z0-9]+)+$', v.lower()):
            log.error("variable must start with HILBERT/hilbert and contain words separated by underscores!"
                  " Input: '{}" .format(d))
            _ret = False

        if _ret:
            self.set_data(v)

        return _ret


###############################################################
class ServiceID(BaseID):
    def __init__(self, *args, **kwargs):
        super(ServiceID, self).__init__(*args, **kwargs)


###############################################################
class ApplicationID(BaseID):
    def __init__(self, *args, **kwargs):
        super(ApplicationID, self).__init__(*args, **kwargs)


###############################################################
class GroupID(BaseID):
    def __init__(self, *args, **kwargs):
        super(GroupID, self).__init__(*args, **kwargs)


###############################################################
class StationID(BaseID):
    def __init__(self, *args, **kwargs):
        super(StationID, self).__init__(*args, **kwargs)


###############################################################
class ProfileID(BaseID):
    def __init__(self, *args, **kwargs):
        super(ProfileID, self).__init__(*args, **kwargs)


###############################################################
class PresetID(BaseID):
    def __init__(self, *args, **kwargs):
        super(PresetID, self).__init__(*args, **kwargs)


###############################################################
class AutoDetectionScript(StringValidator):
    def __init__(self, *args, **kwargs):
        super(AutoDetectionScript, self).__init__(*args, **kwargs)
        self._default_input_data = ''


    def check_script(self, script):
        global PEDANTIC

        assert script is not None

        _ret = True
        log.debug('Checking auto-detection script: {}'.format(script))

        # NOTE: trying to check the BASH script: shellcheck & bash -n 'string':
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(script)

            _cmd = ["bash", "-n", path]
            try:
                # NOTE: Check for valid bash script
                retcode = _execute(_cmd)
            except:
                log.exception("Error while running '{}' to check auto-detection script!".format(' '.join(_cmd)))
                return False  #                if PEDANTIC:  # TODO: add a special switch?

            if retcode != 0:
                log.error("Error while running '{0}' to check auto-detection script: {1}!".format(' '.join(_cmd), retcode))
                return False

            # NOTE: additionall tool: shellcheck (haskell!)
            # FIXME: what if this tool is missing!? TODO: Check for it once!
            _cmd = ["shellcheck", "-s", "bash", path]
            try:
                # NOTE: Check for valid bash script
                retcode = _execute(_cmd)
            except:
                log.exception("Error while running '{}' to check auto-detection script!".format(' '.join(_cmd)))
                return False

            if retcode != 0:
                log.error("Error while running '{0}' to check auto-detection script: {1}!".format(' '.join(_cmd), retcode))
                return False

        finally:
            os.remove(path)

        return True

    def validate(self, d):
        """check whether data is a valid script"""

        global PEDANTIC

        if d is None:
            d = self._default_input_data

        if (d is None) or (d == '') or (d == text_type('')):
            self.set_data(text_type(''))
            return True

        script = ''
        try:
            script = StringValidator.parse(d, parent=self, parsed_result_is_data=True)

            if not bool(script):  # NOTE: empty script is also fine!
                self.set_data(script)
                return True
        except:
            log.exception("Wrong input to AutoDetectionScript::validate: {}". format(d))
            return False


        if not self.check_script(script):
            if PEDANTIC:
                log.error("Bad script: {0}".format(script))
                return False
            else:
                log.warning("Bad script: {0}".format(script))

        self.set_data(script)
        return True


###############################################################
class DockerComposeServiceName(StringValidator):  # TODO: any special checks here?

    def __init__(self, *args, **kwargs):
        super(DockerComposeServiceName, self).__init__(*args, **kwargs)

    def validate(self, d):
        """check whether data is a valid service name in file due to DockerComposeRef"""
        if d is None:
            d = self._default_input_data

        try:
            n = StringValidator.parse(d, parent=self, parsed_result_is_data=True)
            self.set_data(n)
            return True
        except:
            log.error("Wrong input to DockerComposeServiceName::validate: '{}'". format(d))
            return False

###############################################################
class DockerComposeRef(URI):

    def __init__(self, *args, **kwargs):
        super(DockerComposeRef, self).__init__(*args, **kwargs)

        self._default_input_data = text_type('docker-compose.yml')

    def validate(self, d):
        """check whether data is a valid docker-compose file name"""
        if d is None:
            d = self._default_input_data

        # TODO: call docker-compose on the referenced file! Currently in DockerService!?

        return super(DockerComposeRef, self).validate(d)


###############################################################
class Icon(URI):
    def __init__(self, *args, **kwargs):
        super(Icon, self).__init__(*args, **kwargs)

    def validate(self, d):
        """check whether data is a valid icon file name"""

        if d is None:
            d = self._default_input_data

        # TODO: FIXME: check the file contents (or extention)
        return super(Icon, self).validate(d)


###############################################################
class HostAddress(StringValidator):
    """SSH alias"""

    def __init__(self, *args, **kwargs):
        kwargs['parsed_result_is_data'] = kwargs.pop('parsed_result_is_data', False)
        super(HostAddress, self).__init__(*args, **kwargs)

    def validate(self, d):
        """check whether data is a valid ssh alias?"""
        global PEDANTIC

        if d is None:
            d = self._default_input_data

        _h = StringValidator.parse(d, parent=self, parsed_result_is_data=True)

        if _h.startswith("'") and _h.endswith("'"):
            _h = _h[1:-1]
        if _h.startswith('"') and _h.endswith('"'):
            _h = _h[1:-1]

        if PEDANTIC:
            if not self.check_ssh_alias(_h, shell=False, timeout=2):
                return False

        self.set_data(_h)
        return True

    def get_ip_address(self):
        pass

    def get_address(self):
        return self.get_data()

    def recheck(self):
        return self.check_ssh_alias(self.get_address())

    # TODO: check/use SSH/SCP calls!
    def scp(self, source, target, **kwargs):
        global PEDANTIC

        assert self.recheck()
        _h = self.get_address()  # 'jabberwocky' #

        _cmd = shlex.split("scp -q -F {3} {0} {1}:{2}".format(source, _h, target, os.path.join(os.environ['HOME'], ".ssh", "config")))
        __cmd = ' '.join(_cmd)

        #            client = paramiko.SSHClient()
        #            client.load_system_host_keys()
        try:
            retcode = _execute(_cmd, **kwargs)
        except:
            log.exception("Could not execute '{0}'! Exception: {1}".format(__cmd, sys.exc_info()))
            if not PEDANTIC:
                return
            raise

        assert retcode is not None
        if not retcode:
            log.debug("Command ({}) execution success!".format(__cmd))
            return
        else:
            log.error("Could not run scp command: '{0}'! Return code: {1}".format(__cmd, retcode))
            if PEDANTIC:
                raise Exception("Could not run scp command: '{0}'! Exception: {1}".format(__cmd, sys.exc_info()))

    def ssh(self, cmd, **kwargs):
        global PEDANTIC

        assert self.recheck()
        _h = self.get_address()  # 'jabberwocky'

        # TODO: maybe respect SSH Settings for the parent station!?

        _cmd = shlex.split("ssh -q -F {2} {0} {1}".format(_h, ' '.join(cmd), os.path.join(os.environ['HOME'], ".ssh", "config")))
        __cmd = ' '.join(_cmd)

        #            client = paramiko.SSHClient()
        #            client.load_system_host_keys()
        try:
            retcode = _execute(_cmd, **kwargs)
        except:
            log.exception("Could not execute '{0}'! Exception: {1}".format(__cmd, sys.exc_info()))
            raise

        assert retcode is not None
        if not retcode:
            log.debug("Command ({}) execution success!".format(__cmd))
            return
        else:
            log.error("Could not run remote ssh command: '{0}'! Return code: {1}".format(__cmd, retcode))
#            if PEDANTIC:
            raise Exception("Could not run remote ssh command: '{0}'! Exception: {1}".format(__cmd, sys.exc_info()))


    @classmethod
    def check_ssh_alias(cls, _h, **kwargs):
        """Check for ssh alias"""
        global PEDANTIC

        log.debug("Checking ssh alias: '{0}'...".format(text_type(_h)))
        try:
#            client = paramiko.SSHClient()
#            client.load_system_host_keys()

            _cmd = ["ssh", "-q", "-F", os.path.join(os.environ['HOME'], ".ssh", "config"), "-o", "ConnectTimeout=1", _h, "exit 0"]
            retcode = _execute(_cmd, **kwargs)  # , stdout=open("/dev/null", 'w'), stderr=open("/dev/null", 'w')

            if retcode:
                log.warning("Non-functional ssh alias: '{0}' => exit code: {1}!".format(text_type(_h), retcode))
            else:
                log.debug("Ssh alias '{0}' is functional!" . format(text_type(_h)))

            return retcode == 0
        except:
            log.exception("Non-functional ssh alias: '{0}'. Moreover: Unexpected error: {1}" . format(text_type(_h), sys.exc_info()))
            if PEDANTIC:
                raise

            return False


###############################################################
class HostMACAddress(StringValidator):
    """MAC Address of the station"""

    def __init__(self, *args, **kwargs):
        super(HostMACAddress, self).__init__(*args, **kwargs)

    def validate(self, d):
        """check whether data is a valid ssh alias?"""

        if d is None:
            d = self._default_input_data

        v = StringValidator.parse(d, parent=self)

        if not re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", v.lower()):
            _value_error(None, d, d.lc, "ERROR: Wrong MAC Address: [{}]")
            return False

        # TODO: verify the existence of that MAC address?
        self.set_data(v)
        return True

###############################################################
class BoolValidator(ScalarValidator):
    def __init__(self, *args, **kwargs):
        super(BoolValidator, self).__init__(*args, **kwargs)

    def validate(self, d):
        """check whether data is a valid string"""

        if d is None:
            d = self._default_input_data

        if not isinstance(d, bool):
            log.error("not a boolean value: '{}'" . format(d))
            return False

        self.set_data(d)
        return True


class StationVisibility(BoolValidator):  ## "hidden": True / [False]
    def __init__(self, *args, **kwargs):
        super(StationVisibility, self).__init__(*args, **kwargs)
        self._default_input_data = False


class AutoTurnon(BoolValidator):  # Bool, False
    def __init__(self, *args, **kwargs):
        super(AutoTurnon, self).__init__(*args, **kwargs)
        self._default_input_data = False  # no powering on by default!?


###############################################################
class VariadicRecordWrapper(BaseValidator):
    """VariadicRecordWrapper record. Type is determined by the given 'type' field."""

    def __init__(self, *args, **kwargs):
        kwargs['parsed_result_is_data'] = kwargs.pop('parsed_result_is_data', True)
        super(VariadicRecordWrapper, self).__init__(*args, **kwargs)

        self._type_tag = text_type('type')
        self._type_cls = None

        self._default_type = None
        self._types = {}

    # TODO: make sure to use its .parse instead of .validate due to substitution in Wrapper objects!
    def validate(self, d):
        """determine the type of variadic data for the format version"""

        if d is None:
            d = self._default_input_data

        _ret = True
        assert isinstance(d, dict)

        assert self._default_type is not None
        assert self._default_type in self._types

        _rule = self._types[self._default_type]  # Version dependent!
        assert _rule is not None

        assert self._type_cls is not None

        if self._type_tag not in d:
            _lc = d.lc  # start of the current mapping
            _key_error(self._type_tag, d, _lc, "ERROR: Missing mandatory key `{}`")
            return False

        t = None
        try:
            t = self._type_cls.parse(d[self._type_tag], parent=self.get_parent(), parsed_result_is_data=True)
        except:
            log.exception("Wrong type data: {}".format(d[self._type_tag]))
            return False

        if t not in _rule:
            _lc = d.lc  # start of the current mapping
            _key_error(self._type_tag, t, _lc, "ERROR: unsupported/wrong variadic type: '{}'")
            return False

        tt = _rule[t](parent=self.get_parent())

        if not tt.validate(d):
            _lc = d.lc.key(self._type_tag)
            _value_error('*', d, _lc, "ERROR: invalid mapping value '{}' for type '%s'" % t)
            return False

        self.set_data(tt)  # TODO: completely replace this with tt??? access Methods?
        return True


###############################################################
class StationPowerOnMethodWrapper(VariadicRecordWrapper):
    """StationPowerOnMethod :: Wrapper"""

    def __init__(self, *args, **kwargs):
        super(StationPowerOnMethodWrapper, self).__init__(*args, **kwargs)

        T = StationPowerOnMethodType

        self._type_cls = T
        _wol_dm = {T.parse("WOL", parsed_result_is_data=True): WOL, T.parse("DockerMachine", parsed_result_is_data=True): DockerMachine}

        self._default_type = "default_poweron_wrapper"
        self._types[self._default_type] = _wol_dm


###############################################################
class ServiceWrapper(VariadicRecordWrapper):
    """Service :: Wrapper"""

    def __init__(self, *args, **kwargs):
        super(ServiceWrapper, self).__init__(*args, **kwargs)

        T = ServiceType
        self._type_cls = T
        _dc = {T.parse("compose", parsed_result_is_data=True): DockerComposeService}

        self._default_type = "default_docker_compose_service_wrapper"
        self._types[self._default_type] = _dc


###############################################################
class ApplicationWrapper(ServiceWrapper):
    """Application :: Wrapper"""

    def __init__(self, *args, **kwargs):
        super(ApplicationWrapper, self).__init__(*args, **kwargs)

        t = ServiceType  # NOTE: same for docker-compose Services and Applications!
        self._type_cls = t
        _dc = {t.parse("compose", parsed_result_is_data=True): DockerComposeApplication}

        self._default_type = "default_docker_compose_application_wrapper"
        self._types[self._default_type] = _dc


###############################################################
class DockerMachine(BaseRecordValidator):
    """DockerMachine :: StationPowerOnMethod"""

    # _DM = 'docker-machine'
    _HILBERT_STATION = '~/bin/hilbert-station'  # TODO: look at station for this..?

    def __init__(self, *args, **kwargs):
        super(DockerMachine, self).__init__(*args, **kwargs)

        self._type_tag = text_type('type')
        self._vm_host_address_tag = text_type('vm_host_address')
        self._vm_name_tag = text_type('vm_name')

        self._default_type = 'DockerMachine'

        DM_rule = {
            self._type_tag: (True, StationPowerOnMethodType),  # Mandatory!
            text_type('auto_turnon'): (False, AutoTurnon),
            self._vm_name_tag: (True, StringValidator),
            self._vm_host_address_tag: (True, HostAddress)
        }

        self._types = {self._default_type: DM_rule}  # ! NOTE: AMT - maybe later...

    def get_vm_name(self):
        _d = self.get_data()
        assert _d is not None
        _a = _d.get(self._vm_name_tag, None)
        if (_a is None) or (not bool(_a)):
            log.error('Missing vm_name!')
            raise Exception('Missing vm_name!')

        if _a.startswith("'") and _a.endswith("'"):
            _a = _a[1:-1]
        if _a.startswith('"') and _a.endswith('"'):
            _a = _a[1:-1]

        return _a


    def get_vm_host_address(self):
        _d = self.get_data()
        assert _d is not None
        _a = _d.get(self._vm_host_address_tag, None)
        if (_a is None) or (not bool(_a)):
            log.error('Missing vm_host_address!')
            raise Exception('Missing vm_host_address!')

        return _a

    def start(self):  # , action, action_args):
        global PEDANTIC

        _a = self.get_vm_host_address()
        assert _a is not None
        assert isinstance(_a, HostAddress)

        _n = self.get_vm_name()

        # DISPLAY =:0
        _cmd = [self._HILBERT_STATION, 'dm_start', _n]  # self._DM
        try:
            _ret = _a.ssh(_cmd, shell=True)
        except:
            s = "Could not power-on virtual station {0} (at {1})".format(_n, _a)
            if not PEDANTIC:
                log.warning(s)
                return False
            else:
                log.exception(s)
                raise

        return _ret

        # process call: ssh to vm_host + docker-machione start vm_id
#        raise NotImplementedError("Running 'docker-machine start' action is not supported yet... Sorry!")


class WOL(BaseRecordValidator):
    """WOL :: StationPowerOnMethod"""

    _WOL = 'wakeonlan'

    def __init__(self, *args, **kwargs):
        super(WOL, self).__init__(*args, **kwargs)

        self._type_tag = text_type('type')
        self._default_type = 'WOL'
        self._MAC_tag = text_type('mac')

        WOL_rule = {
            self._type_tag: (True, StationPowerOnMethodType),  # Mandatory!
            text_type('auto_turnon'): (False, AutoTurnon),
            self._MAC_tag: (True, HostMACAddress)
        }

        self._types = {self._default_type: WOL_rule}

    def get_MAC(self):
        _d = self.get_data()
        assert _d is not None
        _MAC = _d.get(self._MAC_tag, None)
        assert _MAC is not None
        assert _MAC != ''
        return _MAC



    def start(self):  # , action, action_args):
        global PEDANTIC

        _address = None
        _parent = self.get_parent(cls=Station)

        if _parent is not None:
            if isinstance(_parent, Station):
                _address = _parent.get_address()
                assert _address is not None
                assert isinstance(_address, HostAddress)
                _address = _address.get_address()

        _MAC = self.get_MAC()

        if (_address is None) or (_address == ''):
            log.warning("Sorry: could not get station's address for this WOL MethodObject!")
            _cmd = [self._WOL, _MAC]
            if PEDANTIC:
                raise Exception("Sorry: could not get station's address for this WOL MethodObject!")
        else:
            _cmd = [self._WOL, "-i", _address, _MAC]  # IP?

        __cmd = ' '.join(_cmd)
        try:
            retcode = _execute(_cmd, shell=False)
            assert retcode is not None
            if not retcode:
                log.debug("Command ({}) execution success!".format(__cmd))
                return
            else:
                log.error("Could not poweron via '{0}'! Return code: {1}".format(__cmd, retcode))
                if PEDANTIC:
                    raise Exception("Could not execute '{0}'! Exception: {1}".format(__cmd, sys.exc_info()))
        except:
            log.exception("Could not execute '{0}'! Exception: {1}".format(__cmd, sys.exc_info()))
            if not PEDANTIC:
                return
            raise


###############################################################
class DockerComposeService(BaseRecordValidator):
    """DockerCompose :: Service data type"""

    _DC = "docker-compose"

    def __init__(self, *args, **kwargs):
        super(DockerComposeService, self).__init__(*args, **kwargs)

        self._type_tag = text_type('type')
        self._hook_tag = text_type('auto_detections')
        self._name_tag = text_type('ref')
        self._file_tag = text_type('file')

        _compose_rule = {
            self._type_tag: (True, ServiceType),  # Mandatory
            self._hook_tag: (False, AutoDetectionScript),
            self._name_tag: (True, DockerComposeServiceName),
            self._file_tag: (False, DockerComposeRef)
        }

        self._default_type = "default_dc_service"
        self._types = {self._default_type: _compose_rule}

        self._create_optional = True

    def check_service(self, _f, _n):
        global PEDANTIC

        # TODO: Check the corresponding file for such a service -> Service in DockerService!
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
               _cmd = [self._DC, "-f", _f, "config"]  # TODO: use '--services'?
               try:
                   retcode = _execute(_cmd, shell=False, stdout=tmp, stderr=open("/dev/null", 'w'))
               except:
                   log.exception("Exception while running '{}'!".format(' '.join(_cmd)))
                   return False
#                   _ret = not PEDANTIC  # TODO: add a special switch?

            if retcode:
                return False

            with open(path, 'r') as tmp:
                dc = load_yaml(tmp)  # NOTE: loading external Docker-Compose's YML file using our validating loader!
                ss = None
                for k in dc['services']:
                    if k == _n:
                        ss = dc['services'][k]
                        break

                if ss is None:
                    log.error("missing service/application '{}' in file '{}' !".format(_n, _f))
                    return False
        finally:
            os.remove(path)

        return True

    def validate(self, d):
        global PEDANTIC

        if d is None:
            d = self._default_input_data

        if not BaseRecordValidator.validate(self, d):  # TODO: use .parse?
            assert self.get_data() is None
            return False

        _d = self.get_data()

        # TODO: remove Validators (BaseString) from strings used as dict keys!
        _f = _d[self._file_tag]

        while isinstance(_f, BaseValidator):
            _f = _f.get_data()

        _n = _d[self._name_tag]
        while isinstance(_n, BaseValidator):
            _n = _n.get_data()

        if not os.path.exists(_f):  # TODO: FIXME: use URI::check() instead??
            if PEDANTIC:
                log.error("Missing file with docker-compose configuration: '%s'", _f)
                return False
            log.warning("Missing file with docker-compose configuration: '{0}'. Cannot check the service reference id: '{1}'" .format(_f, _n))
            return True

        if not self.check_service(_f, _n):
            if PEDANTIC:
                log.error("Bad service {0} in {1}".format(_n, _f))
                return False
            else:
                log.warning("Bad service {0} in {1}".format(_n, _f))

        return True  # _ret


###############################################################
class DockerComposeApplication(DockerComposeService):
    """DockerCompose :: Application"""

    def __init__(self, *args, **kwargs):
        super(DockerComposeApplication, self).__init__(*args, **kwargs)

        _compose_rule = (self._types[self._default_type]).copy()

        _compose_rule.update({
            text_type('name'): (True, BaseUIString),  # NOTE: name for UI!
            text_type('description'): (True, BaseUIString),
            text_type('icon'): (False, Icon),
            text_type('compatibleStations'): (True, Group)
        })

        self._types[self._default_type] = _compose_rule

        # TODO: FIXME: add application to compatibleStations!

###############################################################
class Profile(BaseRecordValidator):
    """Profile"""

    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)

        self._default_type = "default_profile"

        default_rule = {
            text_type('name'): (True, BaseUIString),
            text_type('description'): (True, BaseUIString),
            text_type('icon'): (False, Icon),
            text_type('services'): (True, ServiceList),
            text_type('supported_types'): (False, ServiceTypeList)
        }

        self._types = {self._default_type: default_rule}

        self._station_list = None  # TODO: FIXME!


###############################################################
class StationSSHOptions(BaseRecordValidator):  # optional: "Station::ssh_options" # record: user, port, key, key_ref
    """StationSSHOptions"""

    def __init__(self, *args, **kwargs):
        super(StationSSHOptions, self).__init__(*args, **kwargs)

        self._default_type = "default_station_ssh_options"

        default_rule = {
            text_type('user'): (False, StringValidator),
            text_type('key'): (False, StringValidator),
                text_type('port'): (False, StringValidator),
        # TODO: BaseInt??  http://stackoverflow.com/questions/4187185/how-can-i-check-if-my-python-object-is-a-number
            text_type('key_ref'): (False, URI),
        }

        self._types = {self._default_type: default_rule}

    def validate(self, d):
        """check whether data is a valid ssh connection options"""

        if d is None:
            d = self._default_input_data

        _ret = super(StationSSHOptions, self).validate(d)

        # TODO: Check for ssh connection: Use some Python SSH Wrapper (2/3)
        return _ret

###############################################################
class StationType(BaseEnum):
    """Type of station defines the set of required data fields!"""

    def __init__(self, *args, **kwargs):
        super(StationType, self).__init__(*args, **kwargs)

        # NOTE: the list of possible values of Station::type (will depend on format version)
        self._default_input_data = text_type('hidden')  # NOTE: nothing is required. For extension only!
        self._enum_list = [self._default_input_data,
                           text_type('standalone'),  # No remote control via SSH & Hilbert client...
                           text_type('server'),  # Linux with Hilbert client part installed but no remote control!
                           text_type('standard')  # Linux with Hilbert client part installed!
                           ]  # ,text_type('special')


###############################################################
class Station(BaseRecordValidator):  # Wrapper?
    """Station"""

    _extends_tag = text_type('extends')
    _client_settings_tag = text_type('client_settings')
    _type_tag = text_type('type')

    _HILBERT_STATION = '~/bin/hilbert-station'

    def __init__(self, *args, **kwargs):
        super(Station, self).__init__(*args, **kwargs)

        self._poweron_tag = text_type('poweron_settings')
        self._ssh_options_tag = text_type('ssh_options')
        self._address_tag = text_type('address')
        self._ishidden_tag = text_type('hidden')  # TODO: deprecate with "fake" station type?
        self._profile_tag = text_type('profile')

        self._default_type = "default_station"
        default_rule = {
            Station._extends_tag: (False, StationID),
            text_type('name'): (True, BaseUIString),
            text_type('description'): (True, BaseUIString),
            text_type('icon'): (False, Icon),
            self._profile_tag: (True, ProfileID),
            self._address_tag: (True, HostAddress),
            self._poweron_tag: (False, StationPowerOnMethodWrapper),  # !! variadic, PowerOnType...
            self._ssh_options_tag: (False, StationSSHOptions),  # !!! record: user, port, key, key_ref
            text_type('omd_tag'): (True, StationOMDTag),  # ! like ServiceType: e.g. agent. Q: Is this mandatory?
            self._ishidden_tag: (False, StationVisibility),  # Q: Is this mandatory?
            Station._client_settings_tag: (False, StationClientSettings),  # IDMap : (BaseID, BaseString)
            Station._type_tag: (False, StationType)
        }  #

        self._types = {self._default_type: default_rule}

        self._compatible_applications = None  # TODO: FIXME!

        self._HILBERT_STATION = '~/bin/hilbert-station'

    def is_hidden(self):
        _d = self.get_data()
        assert _d is not None

        _h = _d.get(self._ishidden_tag, None)

        if _h is None:
            _h = StationVisibility.parse(None, parent=self, parsed_result_is_data=True)

        return _h

    def get_profile(self):
        _d = self.get_data()
        assert _d is not None
        _profile_id = _d.get(self._profile_tag, None)

        assert _profile_id is not None
        assert _profile_id != ''

        _parent = self.get_parent(cls=Hilbert)
        assert isinstance(_parent, Hilbert)

        _profile = _parent.query('Profiles/{}/all' . format(_profile_id))
        assert _profile is not None
        assert isinstance(_profile, Profile)
        return _profile

    def get_address(self):  # TODO: IP?
        _d = self.get_data()
        assert _d is not None
        _a = _d.get(self._address_tag, None)
        if (_a is None) or (not bool(_a)):
            log.error('Missing station address!')
            raise Exception('Missing station address!')

        assert isinstance(_a, HostAddress)

        log.debug('HostAddress: {}'.format(_a))
        return _a

    def shutdown(self):
        global PEDANTIC

        _a = self.get_address()

        assert _a is not None
        assert isinstance(_a, HostAddress)

        try:
            _ret = _a.ssh([self._HILBERT_STATION, "stop"], shell=False)
        except:
            s = "Could not shutdown station {}".format(_a)
            if not PEDANTIC:
                log.warning(s)
                return False
            else:
                log.exception(s)
                raise

        return _ret

    def deploy(self):
        global PEDANTIC


        # TODO: get_client_settings()
        _d = self.get_data()
        _settings = _d.get(self._client_settings_tag, None)

        if _settings is None:
            if not PEDANTIC:
                log.warning('Missing client settings for this station. Nothing to deploy!')
            else:
                log.error('Missing client settings for this station. Nothing to deploy!')
                raise Exception('Missing client settings for this station. Nothing to deploy!')

        if isinstance(_settings, BaseValidator):
            _settings = _settings.get_data()

        default_app_id = _settings.get('hilbert_station_default_application', None)
        # TODO: check default_app_id!
        # TODO: all compatible applications!?

        _profile = self.get_profile()
        if isinstance(_profile, BaseValidator):
            _profile = _profile.get_data()

        # All supported applications??!?
        _serviceIDs = _profile.get(text_type('services'), [])  # TODO: profile.get_services()
        assert _serviceIDs is not None
        assert isinstance(_serviceIDs, ServiceList)  # list of ServiceID

        _serviceIDs = _serviceIDs.get_data()
        assert isinstance(_serviceIDs, list)  # list of strings (with ServiceIDs)?

        _a = self.get_address()

        assert _a is not None
        assert isinstance(_a, HostAddress)

        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                # TODO: FIXME: list references into docker-compose.yml???
                # TODO: use bash array to serialize all Services/Applications!
                # NOTE: Only handles (IDs) are to be used below:
                # NOTE: ATM only compose && Application/ServiceIDs == refs to the same docker-compose.yml!
                # TODO: NOTE: may differ depending on Station::type!
                tmp.write("hilbert_station_profile_services=\"{}\"\n".format(' '.join(_serviceIDs)))
                for k in _settings:
                    tmp.write("{0}=\"{1}\"\n".format(k, str(_settings.get(k, ''))))
                tmp.write("background_services=\"${hilbert_station_profile_services}\"\n")
                tmp.write("default_app=\"${hilbert_station_default_application}\"\n")
                # TODO: collect all compatible applications!
                tmp.write("possible_apps=\"${default_app}\"\n")

            # TODO: add also all further necessary resources (docker-compose.yml etc) and tar.gz it for deployment?!
            #            _cmd = ["scp", path, "{0}:/tmp/{1}".format(_a, os.path.basename(path))]  # self._HILBERT_STATION, 'deploy'


            try:
                _a.scp(path, "/tmp/{}".format(os.path.basename(path)), shell=False)
            except:
                s = "Could not deploy new local settings to {}".format(_a)
                if not PEDANTIC:
                    log.warning(s)
                    return False
                else:
                    log.exception(s)
                    raise
        finally:
            log.debug("Temporary Station Configuration File: {}".format(path))
#            s = ''
#            with os.open(path, 'r') as tmp:
#                s += tmp.readline() + '\n'
#            log.debug("New Station Configuration: {}".format(s))
#            os.remove(path)

        _cmd = [self._HILBERT_STATION, "prepare", os.path.join("/tmp", os.path.basename(path))]
        try:
            _a.ssh(_cmd, shell=False)
        except:
            s = "Could not prepare the station using the new configuration file with {}".format(' '.join(_cmd))
            if not PEDANTIC:
                log.warning(s)
                return False
            else:
                log.exception(s)
                raise

        #        ### see existing deploy.sh!?
        # TODO: what about other external resources? docker-compose*.yml etc...?
        # TODO: restart hilbert-station?

#        raise NotImplementedError("Cannot deploy local configuration to this station!")

#    def start_service(self, action_args):
#        raise NotImplementedError("Cannot start a service/application on this station!")

#    def finish_service(self, action_args):
#        raise NotImplementedError("Cannot finish a service/application on this station!")

    def app_switch(self, app_id):
        global PEDANTIC

        _a = self.get_address()

        assert _a is not None
        assert isinstance(_a, HostAddress)

        try:
            _ret = _a.ssh([self._HILBERT_STATION, "app_switch", app_id], shell=False)
        except:
            s = "Could not change top application on the station '{0}' to '{1}'".format(_a, app_id)
            if not PEDANTIC:
                log.warning(s)
                return False
            else:
                log.exception(s)
                raise

        return _ret

#        raise NotImplementedError("Cannot switch to a different application on this station!")

    def poweron(self):
        _d = self.get_data()
        assert _d is not None

        poweron = _d.get(self._poweron_tag, None)
        if poweron is None:
            log.error("Missing/wrong Power-On Method configuration for this station!")
            raise Exception("Missing/wrong Power-On Method configuration for this station!")

        poweron.start()  # , action_args????

    def run_action(self, action, action_args):
        """
        Run the given action on/with this station

        :param action_args: arguments to the action
        :param action:
                start  (poweron)
                stop  (shutdown)
                cfg_deploy
                app_change <ApplicationID>
#                start [<ServiceID/ApplicationID>]
#                finish [<ServiceID/ApplicationID>]

        :return: nothing.
        """

        if action not in ['start', 'stop', 'cfg_deploy', 'app_change']:
            raise Exception("Running action '{0}({1})' is not supported!" . format(action, action_args))

        # Run 'ssh address hilbert-station action action_args'?!
        if action == 'start':
            self.poweron()  # action_args
        elif action == 'cfg_deploy':
            self.deploy()  # action_args
        elif action == 'stop':
            self.shutdown()  # action_args
        elif action == 'app_change':
            self.app_switch(action_args)  # ApplicationID

#        elif action == 'start':
#            self.start_service(action_args)
#        elif action == 'finish':
#            self.finish_service(action_args)


    def get_base(self):
        _d = self.get_data()
        assert _d is not None
        _b = _d.get(self._extends_tag, None)  # StationID (validated...)

#        if _b is not None:
#            if isinstance(_b, BaseValidator):
#                _b = _b.get_data()

        return _b

    def extend(delta, base):  # delta == self!
        assert delta.get_base() is not None
        assert base.get_base() is None

        # NOTE: at early stage there may be no parent data...
        if delta.get_parent() is not None:
            if delta.get_parent().get_data() is not None:
                assert delta.get_base() in delta.get_parent().get_data()
                assert delta.get_parent().get_data().get(delta.get_base(), None) == base

        _d = delta.get_data()
        _b = base.get_data()

        assert delta._extends_tag in _d
        assert delta._extends_tag not in _b

        del _d[delta._extends_tag]
        assert delta.get_base() is None

        # NOTE: Extend/merge the client settings:
        k = delta._client_settings_tag

        bb = _b.get(k, None)
        if bb is not None:
            dd = _d.get(k, None)
            if dd is None:
                dd = StationClientSettings.parse(None, parent=delta)

            assert isinstance(dd, StationClientSettings)
            assert isinstance(bb, StationClientSettings)
            dd.extend(bb)

            _d[k] = dd

        # NOTE: the following is an application of delta to base data
        for k in _b:  # NOTE: take from base only the missing parts
            assert k != delta._extends_tag

            if k == delta._client_settings_tag:
                continue

            v = _d.get(k, None)

            if v is None:  # key from base is missing or None in delte?
                _d[k] = _b[k]  # TODO: is copy() required for complicated structures?


###############################################################
class BaseIDMap(BaseValidator):
    """Mapping: SomeTypeID -> AnyType"""

    def __init__(self, *args, **kwargs):
        super(BaseIDMap, self).__init__(*args, **kwargs)

        self._default_type = None
        self._types = {}  # type -> (TypeID, Type)

        self._default_input_data = {}

    def detect_type(self, d):
        """determine the type of variadic data for the format version"""

        assert not (self._default_type is None)
        assert len(self._types) > 0

        return self._default_type

    def validate(self, d):
        if d is None:
            d = self._default_input_data

        assert isinstance(d, dict)

        self._type = self.detect_type(d)

        assert self._type is not None
        assert self._type in self._types

        (_id_rule, _rule) = self._types[self._type]

        try:
            _lc = d.lc  # starting position?
        except:
            log.warning("Input data bears no ruamel.yaml line/column data!")
            _lc = (0, 0)

        (s, c) = _get_line_col(_lc)

        _d = {}

        _ret = True
        for offset, k in enumerate(d):
            v = d[k]  # TODO: d[offset]???
            l = s + offset
            _lc = (l, c)

            _id = None
            _vv = None

            try:
                _id = _id_rule.parse(k, parent=self)
            except ConfigurationError as err:
                _key_error(k, v, _lc, "Invalid ID: '{}' (type: '%s')" % (self._type))  # Raise Exception?
                pprint(err)
                _ret = False

            try:
                _vv = _rule.parse(v, parent=self)
            except ConfigurationError as err:
                _value_error(k, v, _lc, "invalid Value (for ID: '{}') (type: '%s')" % (self._type))  # Raise Exception?
                pprint(err)
                _ret = False

            if _ret:
                assert _id is not None
                assert _vv is not None
                # _id = _id.get_data() # ??
                _d[_id] = _vv  # .get_data()

        if _ret:
            self.set_data(_d)

        return _ret


###############################################################
class GlobalServices(BaseIDMap):
    def __init__(self, *args, **kwargs):
        super(GlobalServices, self).__init__(*args, **kwargs)

        self._default_type = "default_global_services"
        self._types = {self._default_type: (ServiceID, ServiceWrapper)}

        # def validate(self, data):
        #     _ret = BaseID.validate(self, data)
        #     ### TODO: Any post processing?
        #     return _ret


###############################################################
# "client_settings": (False, StationClientSettings) # IDMap : (BaseID, BaseString)
class StationClientSettings(BaseIDMap):
    def __init__(self, *args, **kwargs):
        super(StationClientSettings, self).__init__(*args, **kwargs)

        self._default_type = "default_station_client_settings"
        self._types = {
            self._default_type: (ClientVariable, ScalarValidator)
        }  # ! TODO: only strings for now! More scalar types?! BaseScalar?

    # TODO: FIXME: check for default hilbert applicationId!

    def extend(delta, base):
        assert isinstance(base, StationClientSettings)

        _b = base.get_data()
        if _b is not None:
            assert isinstance(_b, dict)
            _b = _b.copy()

            # NOTE: merge and override settings from the base using the current delta:
            _d = delta.get_data()
            if _d is not None:
                _b.update(_d)

            delta.set_data(_b)


###############################################################
class GlobalApplications(BaseIDMap):
    def __init__(self, *args, **kwargs):
        super(GlobalApplications, self).__init__(*args, **kwargs)

        self._default_type = "default_global_applications"
        self._types = {self._default_type: (ApplicationID, ApplicationWrapper)}

###############################################################
class GlobalProfiles(BaseIDMap):
    def __init__(self, *args, **kwargs):
        super(GlobalProfiles, self).__init__(*args, **kwargs)

        self._default_type = "default_global_profiles"
        self._types = {self._default_type: (ProfileID, Profile)}

        # def validate(self, data):
        #     _ret = BaseID.validate(self, data)
        #     ### TODO: Any post processing?
        #     return _ret


###############################################################
class GlobalStations(BaseIDMap):
    """Global mapping of station IDs to Station's"""

    def __init__(self, *args, **kwargs):
        super(GlobalStations, self).__init__(*args, **kwargs)

        self._default_type = "default_global_stations"
        self._types = {self._default_type: (StationID, Station)}  # NOTE: {StationID -> Station}

    def validate(self, d):
        """Extension mechanism on top of the usual ID Mapping parsing"""

        if d is None:
            d = self._default_input_data

        if not BaseIDMap.validate(self, d):
            return False

        sts = self.get_data()  # NOTE: may be handy for postprocessing!

        _ret = True

        _processed = {}
        _todo = {}

        for k in sts:
            v = sts[k]  # TODO: popitem as below?
            _b = v.get_base()

            if _b is None:  # TODO: FIXME: add to Station API!
                _processed[k] = v
            else:
                assert _b in sts  # NOTE: any station extends some _known_ station!
                _todo[k] = v

        _chg = True
        while bool(_todo) and _chg:
            _chg = False
            _rest = {}
            while bool(_todo):
                k, v = _todo.popitem()

                _b = v.get_base()
                assert k != _b  # no infinite self-recursive extensions!

                # print(_b, ' :base: ', type(_b))
                assert _b in _processed

                if _b in _processed:
                    v.extend(_processed[_b])
                    _processed[k] = v
                    assert v.get_base() is None
                    _chg = True
                else:
                    _rest[k] = v

            _todo = _rest

        if bool(_todo):
            log.error('Cyclic dependencies between stations: {}' .format(_todo))
            _ret = False

#        if _ret:
#            self.set_data(_processed)

        # TODO: FIXME: check for required fields after extension only!!!

        return _ret


###############################################################
class BaseList(BaseValidator):
    """List of entities of the same type"""

    def __init__(self, *args, **kwargs):
        super(BaseList, self).__init__(*args, **kwargs)

        self._default_type = None
        self._types = {}

    def validate(self, d):
        if d is None:
            d = self._default_input_data

        assert self._default_type is not None
        assert len(self._types) > 0

        _lc = d.lc

        # NOTE: determine the class of items based on the version and sample data
        self._type = self._types[self._default_type]
        assert self._type is not None

        if (not isinstance(d, (list, dict, tuple, set))) and isinstance(d, string_types):
            try:
                _d = [self._type.parse(StringValidator.parse(d, parent=self))]
                self.get_data(_d)
                return True
            except:
                pass  # Not a single string entry...

        # list!?
        _ret = True

        _d = []
        for idx, i in enumerate(d):  # What about a string?
            _v = None
            try:
                _v = self._type.parse(i, parent=self)
                _d.insert(idx, _v)  # append?
            except ConfigurationError as err:
                _value_error("[%d]" % idx, d, _lc, "Wrong item in the given sequence!")
                pprint(err)
                _ret = False

        if _ret:
            self.set_data(_d)

        return _ret


###############################################################
class GroupIDList(BaseList):
    """List of GroupIDs or a single GroupID!"""

    def __init__(self, *args, **kwargs):
        super(GroupIDList, self).__init__(*args, **kwargs)

        self._default_type = "default_GroupID_list"
        self._types = {self._default_type: GroupID}


###############################################################
class ServiceList(BaseList):
    """List of ServiceIDs or a single ServiceID!"""

    def __init__(self, *args, **kwargs):
        super(ServiceList, self).__init__(*args, **kwargs)

        self._default_type = "default_ServiceID_list"
        self._types = {self._default_type: ServiceID}


###############################################################
class ServiceTypeList(BaseList):
    """List of ServiceType's or a single ServiceType!"""

    def __init__(self, *args, **kwargs):
        super(ServiceTypeList, self).__init__(*args, **kwargs)

        self._default_type = "default_ServiceType_list"
        self._types = {self._default_type: ServiceType}


###############################################################
class Group(BaseRecordValidator):  # ? TODO: GroupSet & its .parent?
    """Group"""

    def __init__(self, *args, **kwargs):
        super(Group, self).__init__(*args, **kwargs)

        self._default_type = "default_group"

        self._include_tag = text_type('include')
        self._exclude_tag = text_type('exclude')
        self._intersectWith_tag = text_type('intersectWith')

        self._station_list = None  # TODO: FIXME!

        default_rule = {
            self._include_tag: (False, GroupIDList),
            self._exclude_tag: (False, GroupIDList),
            self._intersectWith_tag: (False, GroupIDList)
        }
        # text_type('name'): (False, BaseUIString),
        # text_type('description'): (False, BaseUIString),
        # text_type('icon'): (False, Icon)

        self._types = {self._default_type: default_rule}

    def detect_extra_rule(self, key, value):  # Any extra unlisted keys in the mapping?

        if value is None:  # Set item!
            return GroupID, ScalarValidator

        return None

    def validate(self, d):
        if d is None:
            d = self._default_input_data

        _ret = BaseRecordValidator.validate(self, d)

        # TODO: FIXME: Add extra keys into include!

        return _ret



###############################################################
class GlobalGroups(BaseIDMap):
    def __init__(self, *args, **kwargs):
        super(GlobalGroups, self).__init__(*args, **kwargs)

        self._default_type = "default_global_groups"
        self._types = {self._default_type: (GroupID, Group)}


###############################################################
class Preset(BaseRecordValidator):
    """Preset"""

    def __init__(self, *args, **kwargs):
        super(Preset, self).__init__(*args, **kwargs)

        self._default_type = "default_preset"
        # self.__tag      = "Version"
        default_rule = {
            #     self.__tag:  (True ,  ??), # Mandatory
            #     self.__tag:  (False,  ??), # Optional
        }
        self._types = {self._default_type: default_rule}
        raise NotImplementedError("Presets are not supported yet!")


###############################################################
class GlobalPresets(BaseIDMap):  # Dummy for now!

    def __init__(self, *args, **kwargs):
        super(GlobalPresets, self).__init__(*args, **kwargs)

        self._default_type = "default_global_presets"
        self._types = {self._default_type: (PresetID, Preset)}

    def validate(self, d):
        if d is None:
            d = self._default_input_data

        log.warning("Presets are not supported yet!")
        #        raise NotImplementedError("Presets are not supported yet!")
        return True

###############################################################
class Hilbert(BaseRecordValidator):
    """General Hilbert Configuration format"""

    def __init__(self, *args, **kwargs):
        kwargs['parsed_result_is_data'] = kwargs.pop('parsed_result_is_data', False)

        super(Hilbert, self).__init__(*args, **kwargs)  # This is the Main Root of all Validators!

        self._default_type = "default_global"

        self._version_tag = text_type('Version')
        self._applications_tag = text_type('Applications')
        self._services_tag = text_type('Services')
        self._profiles_tag = text_type('Profiles')
        self._stations_tag = text_type('Stations')
        self._groups_tag = text_type('Groups')

        ### explicit (optional) Type?
        default_rule = {
            self._version_tag: (True, SemanticVersionValidator),  # Mandatory, specifies supported Types of Config's Entity
            self._services_tag: (True, GlobalServices),
            self._applications_tag: (True, GlobalApplications),
            self._profiles_tag: (True, GlobalProfiles),
            self._stations_tag: (True, GlobalStations),
            self._groups_tag: (False, GlobalGroups),  # Optional
            text_type('Presets'): (False, GlobalPresets),  # Optional. May be removed! default?
        }

        self._types = {self._default_type: default_rule}

        self._default_input_data = None

    @classmethod
    def parse(cls, d, *args, **kwargs):
        self = cls(*args, **kwargs)

        if self._version_tag not in d:
            _key_note(self._version_tag, d.lc, "ERROR: Missing mandatory '{}' key field!")
            raise ConfigurationError(u"{}: {}".format("ERROR:", "Missing version tag '{0}' in the input: '{1}'!".format(self._version_tag, d)))

        try:
            _v = SemanticVersionValidator.parse(d[self._version_tag], parent=self, partial=True)
        except:
            _value_error(self._version_tag, d, d.lc, "Wrong value of global '{}' specification!")
            raise

        self.set_version(_v)  # NOTE: globally available now!

        if self.validate(d):  # NOTE: validate should not **explicitly** throw exceptions!!!
            if self._parsed_result_is_data:
                return self.get_data()

            return self

        # NOTE: .parse should!
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data: '{}'!".format(d)))

    def validate(self, d):
        global PEDANTIC
        if d is None:
            d = self._default_input_data

        assert isinstance(d, dict)

        _ret = BaseRecordValidator.validate(self, d)

        for offset, k in enumerate(d):
            if k == self._version_tag:
                if offset != 0:
                    if not PEDANTIC:
                        log.warning("'{}' specified correctly but not ahead of everything else (offset: {})!"
                            .format(self._version_tag, offset))
                    else:
                        log.error("'{}' specified correctly but not ahead of everything else (offset: {})!"
                            .format(self._version_tag, offset))
                        _ret = False
                break

        if not _ret:
            log.error("Wrong Hilbert configuration!")
            return _ret

        _d = self.get_data()
        # NOTE: check uniqueness of keys among (Services/Applications):

        # TODO: add get_service(s) and get_application(s)?
        _services = self.query("{0}/{1}".format(self._services_tag, 'data'))
        _applications = self.query("{0}/{1}".format(self._applications_tag, 'data'))  # _d.get()

        assert _services is not None
        assert _applications is not None

        if (len(_services) > 0) and (len(_applications) > 0):
            for p, k in enumerate(_services):
                if k in _applications:
                    log.error("'{}' is both a ServiceID and an ApplicationID:".format(k))

                    __services = d.get(self._services_tag)  # Rely on the above and use get_data?
                    __applications = d.get(self._applications_tag)

                    _key_error(k, __services[k], __services.lc.key(k), "Service key: {}")
                    _key_error(k, __applications[k], __applications.lc.key(k), "Application key: {}")

                    _ret = False

        # ! TODO: check Uniqueness of keys among (Profiles/Stations/Groups) !!!!
        # ! TODO: check for GroupID <-> StationID <-!=-> ProfileID

        return _ret

###############################################################
def load_yaml(f, Loader=VerboseRoundTripLoader, version=(1, 2), preserve_quotes=True):
    try:
        return yaml.load(f, Loader=Loader, version=version, preserve_quotes=preserve_quotes)
    except (IOError, yaml.YAMLError) as e:
        error_name = getattr(e, '__module__', '') + '.' + e.__class__.__name__
        raise ConfigurationError(u"{}: {}".format(error_name, e))
        

def load_yaml_file(filename):
    with open(filename, 'r') as fh:
        return load_yaml(fh)


###############################################################
def parse_hilbert(d, parent=None):
    assert d is not None
    return Hilbert.parse(d, parent=parent, parsed_result_is_data=False)


###############################################################
def yaml_dump(d, stream=None):
    return yaml.round_trip_dump(d, stream=stream)
