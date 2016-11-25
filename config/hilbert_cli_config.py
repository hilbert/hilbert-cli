# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import logging
log = logging.getLogger(__name__)

# from .helpers import load_yaml, pprint

###############################################################
import pprint as PP
_pp = PP.PrettyPrinter(indent=4)

def pprint(cfg):
#    print("## Validated/Parsed pretty Result: ")
    global _pp
    _pp.pprint(cfg)  # TODO: use loggger?
#    PP.pformat


###############################################################
# NOTE: Global variuables
PEDANTIC = False  # NOTE: to treat invalid values/keys as errors?
INPUT_DIRNAME = './'
# OUTPUT_DIRNAME = INPUT_DIRNAME


###############################################################
up_arrow = '↑'

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

def _key_error(key, value, lc, error_message, e='K'):
    (line, col) = _get_line_col(lc)

    if key is None:
        key = '*'

    print('{}[line: {}, column: {}]: {}'.format(e, line + 1, col + 1, error_message.format(key)))
    print('{}{}: {}'.format(' ' * col, key, value))  #!
    # ! TODO: try to get access to original ruamel.yaml buffered lines...?
    print('{}{}'.format(' ' * col, up_arrow))
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
    print('{}{}: {}'.format(' ' * col, key, value))  #!
    # ! TODO: try to get access to original ruamel.yaml buffered lines...?
    print('{}{}'.format(' ' * val_col, up_arrow))
    print('---')

# Unused???
# def value_warning(key, value, lc, error):
#    _value_error(key, value, lc, error, e='W')


###############################################################
import collections
import ruamel.yaml as yaml

from ruamel.yaml.reader import Reader
from ruamel.yaml.scanner import RoundTripScanner  # Scanner
from ruamel.yaml.parser import RoundTripParser  # Parser,
from ruamel.yaml.composer import Composer
from ruamel.yaml.constructor import RoundTripConstructor  # Constructor, SafeConstructor,
from ruamel.yaml.resolver import VersionedResolver  # Resolver,
# from ruamel.yaml.nodes import MappingNode


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
from ruamel.yaml.compat import PY2, PY3, text_type, string_types, ordereddict
from abc import *
import sys

if PY3 and (sys.version_info[1] >= 4):
    class AbstractValidator(ABC):
        """AbstractValidator is the root Base class for any concrete implementation of entities
        appearing in the general configuration file"""

        @abstractmethod
        def validate(self, d): # TODO: FIXME: change API: return parsed value, throw exception if input is invalid!
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
class Base(AbstractValidator):
    """Abstract Base Class for the Config entities"""

    __version = [None]

    _parent = None

    _data = None
    _default_data = None

    def get_parent(self):
        return self._parent

    def __init__(self, parent):  # TODO: add tag? here or in some child?
        AbstractValidator.__init__(self)
        assert self._parent is None
        self._parent = parent
        self.__API_VERSION_ID = "$Id$"

    def get_api_version(self):
        return self.__API_VERSION_ID
    
    @classmethod
    def set_version(cls, v):
        """To be set once only for any Validator class!"""
        assert len(cls.__version) == 1
        assert cls.__version[0] is None
        cls.__version[0] = v

    @classmethod
    def get_version(cls, default=None):
        assert len(cls.__version) == 1

        if cls.__version[0] is not None:
            return cls.__version[0]

        return default

    def set_data(self, d):
        # assert self._data is None
        # assert d is not None
        self._data = d

    def get_data(self):
        _d = self._data
        if _d is None:
            _d = self._default_data

        return _d

    @classmethod
    def parse(cls, d, parent=None):
        self = cls(parent)

        if d is None:
            d = self._default_data

        if self.validate(d):  # TODO: FIXME: NOTE: validate should not **explicitly** throw exceptions!!!
            return self  # .get_data()

        # NOTE: .parse should!
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data: '{}'!" .format(d)))

    def __repr__(self):
        """Print using pretty formatter"""

        d = self.get_data()  # vars(self) # ???
        return PP.pformat(d, indent=4, width=1)

#    def __str__(self):
#        """Convert to string"""
#
#        d = self.get_data()  # vars(self) # ???
#        return str(d)

    def __eq__(self, other):
        assert isinstance(self, Base)

#        if not isinstance(other, Base):
#            return self.get_data() == other

        assert isinstance(other, Base)

        assert self.get_api_version() == other.get_api_version() # Same /config/hilbert_cli_config.py should be used!
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
                if isinstance(v, Base):
                    v = v.data_dump()
                _dd[k] = v
            return _dd

        if isinstance(_d, list):
            _dd = []
            for idx, i in enumerate(_d):
                v = i
                if isinstance(v, Base):
                    v = v.data_dump()
                _dd.insert(idx,  v)
            return _dd

#        if isinstance(_d, string_types):
        return _d


    def query(self, what):
        """Generic query for data subset about this object"""

        # NOTE: no data dumping here! Result may be a validator!

        log.debug("Querying '%s'", what)


        if (what is None) or (what == ''):
            what = 'all'

        if what == 'all':
            return self

        _d = self.get_data()

        if what == 'keys':
            assert isinstance(_d, dict)
            return _d.keys()

        s = BaseString.parse(what, parent=self)

        if s in _d:
            return _d[s]

        sep = "/"
        ss = s.split(sep)  # NOTE: encode using pathes!

        h = ss[0]  # top header
        t = sep.join(ss[1:])  # tail

        if h in _d:
            d = _d[ss[0]]
            if isinstance(d, Base):
                return d.query(t)  # TODO: FIXME: avoid recursion...

            log.warning("Could not query an object. Ignoring the tail: %s", t)
            return d

        raise ConfigurationError(u"{}: {}".format("ERROR:",
                                                  "Sorry cannot show '{0}' of {1}!".format(what, type(self))))


###############################################################
class BaseRecord(Base):
    """Aggregation of data as a record with some fixed data memebers"""

    # TODO: turn _default_type into a class-member (by moving it here)...?

    def __init__(self, parent):
        Base.__init__(self, parent)
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
                    _k = BaseString.parse(k, parent=self)
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
                    _k = BaseString.parse(k, parent=self)
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
class BaseScalar(Base):
    """Single scalar value out of YAML scalars: strings, numbert etc."""

    def __init__(self, parent):
        Base.__init__(self, parent)

    def validate(self, d):
        """check that data is a scalar: not a sequence or mapping or set"""

        if d is not None:
            if isinstance(d, (list, dict, tuple, set)):  # ! Check if data is not a container?
                print("ERROR: value: '{}' is not a scalar value!!" . format(d))
                return False

            if isinstance(d, string_types):
                d = text_type(d)

        # NOTE: None is also a scalar value...!
        self.set_data(d)
        return True

    @classmethod
    def parse(cls, d, parent=None):
        self = cls(parent)

        if d is None:
            d = self._default_data

        if self.validate(d):  # TODO: FIXME: NOTE: validate should not **explicitly** throw exceptions!!!
            return self.get_data()

        # NOTE: .parse should!
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data: '{}'!" .format(d)))


###############################################################
class BaseString(BaseScalar):
    """YAML String"""
    def __init__(self, parent):
        BaseScalar.__init__(self, parent)
        self._default_data = ''

    def validate(self, d):
        """check whether data is a valid string. Note: should not care about format version"""

        assert d is not None

        s = BaseScalar.parse(d, parent=self)

        if not isinstance(s, string_types):
            print("ERROR: value: '{}' is not a string!!" . format(d))
            return False

        self.set_data(text_type(d))
        return True


###############################################################
# import semver
import semantic_version  # supports partial versions


class SemanticVersion(BaseString):
    def __init__(self, parent, partial=False):
        BaseString.__init__(self, parent)

        self._partial = partial

    def validate(self, d):
        """check the string data to be a valid semantic verions"""

        _t = BaseString.parse(d, parent=self)

        # self.get_version(None) # ???
        _v = None
        try:
            _v = semantic_version.Version(_t, partial=self._partial)
        except:
            print("ERROR: wrong version data: '{0}' (see: '{1}')" . format(d, sys.exc_info()))
            return False

        self.set_data(_v)
        return True

    @classmethod
    def parse(cls, d, parent=None, partial=False):
        self = cls(parent, partial=partial)

        assert d is not None
#            d = self._default_data

        if self.validate(d):  # TODO: FIXME: NOTE: validate should not **explicitly** throw exceptions!!!
            return self  # keep the validator to handle some general actions via its API: e.g. data_dump

        # NOTE: .parse should!
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data: '{}'!" .format(d)))

    def data_dump(self):
        return str(self.get_data())

###############################################################
class BaseUIString(BaseString):  # visible to user => non empty!
    def __init__(self, parent):
        BaseString.__init__(self, parent)
        self._default_data = None

    def validate(self, d):
        """check whether data is a valid string"""
        t = BaseString.parse(d, parent=self)

        if bool(t):  # Non-empty
            self.set_data(t)
            return True

        return False


###############################################################
class BaseEnum(BaseString):  # TODO: Generalize to not only strings...?
    """Enumeration/collection of several fixed strings"""

    def __init__(self, parent):
        BaseString.__init__(self, parent)
        self._enum_list = []  # NOTE: will depend on the version...

    def validate(self, d):
        """check whether data is in the list of fixed strings (see ._enum_list)"""

        t = BaseString.parse(d, parent=self)

        if not (t in self._enum_list): # check withing a list of possible string values
            print("ERROR: string value: '{}' is not among known enum items!!".format(d))
            return False

        self.set_data(t)
        return True


###############################################################
class ServiceType(BaseEnum):  # Q: Is 'Service::type' mandatory? default: 'compose'
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)

        compose = text_type('compose')
        self._enum_list = [compose]  # NOTE: 'docker' and others may be possible later on
        self._default_data = compose


###############################################################
class StationOMDTag(BaseEnum):  # Q: Is 'Station::omd_tag' mandatory? default: 'standalone'
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)

        _v = text_type('standalone')
        self._enum_list = [text_type('agent'), text_type('windows'), _v]  # NOTE: possible values of omd_tag
        self._default_data = _v


###############################################################
class StationPowerOnMethodType(BaseEnum):  # Enum: [WOL], AMTvPRO, DockerMachine
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)

        wol = text_type('WOL')
        # NOTE: the list of possible values of PowerOnMethod::type (will depend on format version)
        self._enum_list = [wol, text_type('DockerMachine')]  # NOTE: 'AMTvPRO' and others may be possible later on
        self._default_data = wol


###############################################################
import os

if PY3:
    from urllib.parse import urlparse
    from urllib.request import urlopen
elif PY2:
    from urlparse import urlparse
    from urllib2 import urlopen


class URI(BaseString):
    """Location of external file, either URL or local absolute or local relative to the input config file"""

    def __init__(self, parent):
        BaseString.__init__(self, parent)
        self._type = None

    def validate(self, d):
        """check whether data is a valid URI"""

        v = BaseString.parse(d, parent=self)

        _ret = True

        if urlparse(v).scheme != '':
            self._type = text_type('url')
            try:
                urlopen(v).close()
            except:
                print("WARNING: URL: '{}' is not accessible!".format(v))
                _ret = not PEDANTIC

        # TODO: FIXME: base location should be the input file's dirname???
#        elif not os.path.isabs(v):
#            v = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), v))

        elif os.path.isfile(v):  # Check whether file exists
            self._type = text_type('file')

        elif os.path.isdir(v):  # Check whether directory exists
            self._type = text_type('dir')

        if not _ret:
            print("WARNING: missing/unsupported resource location: {}".format(v))
            _ret = (not PEDANTIC)

        if _ret:
            self.set_data(v)

        return _ret

    ## TODO: @classmethod check_uri()

    @classmethod
    def parse(cls, d, parent=None):
        self = cls(parent)

        if d is None:
            d = self._default_data

        if self.validate(d):  # TODO: FIXME: NOTE: validate should not **explicitly** throw exceptions!!!
            return self.get_data()  # TODO: due to DockerComposeFile later on :-(

        # NOTE: .parse should!
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data: '{}'!" .format(d)))

###############################################################
import re, tokenize

if PY3:
    def is_valid_id(k):
        return k.isidentifier()
elif PY2:
    def is_valid_id(k):
        return re.match(tokenize.Name + '$', k)
else:
    raise NotImplementedError("Unsupported Python version: '{}'".format(sys.version_info))

###############################################################
class BaseID(BaseString):
    def __init__(self, parent):
        BaseString.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid ID string"""

        v = BaseString.parse(d, parent=self)

        if not is_valid_id(v):
            print("ERROR: not a valid variable identifier! Input: '{}'" . format(d))
            return False

        self.set_data(v)
        return True

###############################################################
class ClientVariable(BaseID):  #
    def __init__(self, parent):
        BaseID.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid ID string"""

        v = BaseID.parse(d, parent=self)  # .get_data()

        _ret = True

        if not (v == v.lower() or v == v.upper()):  # ! Variables are all lower or upper case!
            print("ERROR: a variable must be either in lower or upper case! Input: '{}'" . format(d))
            _ret = False

        # NOTE: starting with hilbert_ or HILBERT_ with letters, digits and '_'??
        if not re.match('^hilbert(_[a-z0-9]+)+$', v.lower()):
            print("ERROR: variable must start with HILBERT/hilbert and contain words separated by underscores!"
                  " Input: '{}" .format(d))
            _ret = False

        if _ret:
            self.set_data(v)

        return _ret


###############################################################
class ServiceID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)


###############################################################
class ApplicationID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)


###############################################################
class GroupID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)


###############################################################
class StationID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)


###############################################################
class ProfileID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)


###############################################################
class PresetID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)


###############################################################
import tempfile

class AutoDetectionScript(BaseString):
    def __init__(self, parent):
        BaseString.__init__(self, parent)
        self._default_data = ''

    def validate(self, d):
        """check whether data is a valid script"""

        if (d is None) or (d == '') or (d == text_type('')):
            self.set_data(text_type(''))
            return True

        script = BaseString.parse(d, parent=self)

        assert bool(script)

        # NOTE: trying to check the BASH script: shellcheck & bash -n 'string':
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(script)

            _cmd = ["bash", "-n", path]
            try:
                # NOTE: Check for valid bash script
                subprocess.check_call(_cmd)  # stdout=open("/dev/null", 'w'), stderr=open("/dev/null", 'w'))
                _ret = True
            except:
                print("WARNING: error running 'bash -n' to check '{0}' (exit code: {1})!" . format(text_type(script), sys.exc_info()))
                _ret = not PEDANTIC # TODO: add a special switch?

            # NOTE: additionall tool: shellcheck (haskell!)
            _cmd = ["shellcheck", "-s", "bash", path]
            try:
                # NOTE: Check for valid bash script
                subprocess.check_call(_cmd)  # stdout=open("/dev/null", 'w'), stderr=open("/dev/null", 'w'))
                _ret = True
            except:
                print("WARNING: error running 'shellcheck' to check '{0}' (exit code: {1})!".format(text_type(script), sys.exc_info()))
                _ret = not PEDANTIC  # TODO: add a special switch?

        finally:
            os.remove(path)

        if _ret:
            self.set_data(script)

        return True


###############################################################
class DockerComposeServiceName(BaseString):
    def __init__(self, parent):
        BaseString.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid service name in file due to DockerComposeRef"""

        n = BaseString.parse(d, parent=self)

        self.set_data(n)
        return True

###############################################################
class DockerComposeRef(URI):
    def __init__(self, parent):
        URI.__init__(self, parent)
        self._default_data = text_type('docker-compose.yml')

    def validate(self, d):
        """check whether data is a valid docker-compose file name"""

        # TODO: call docker-compose on the referenced file! Currently in DockerService!?

        return URI.validate(self, d)


###############################################################
class Icon(URI):
    def __init__(self, parent):
        URI.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid icon file name"""

        # TODO: FIXME: check the file contents (or extention)
        return URI.validate(self, d)


###############################################################
import subprocess  # , shlex
# import paramiko

class HostAddress(BaseString):
    """SSH alias"""

    def __init__(self, parent):
        BaseString.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid ssh alias?"""

        _h = BaseString.parse(d, parent=self)

        if not self.check_ssh_alias(_h):
            if PEDANTIC:
                return False

        self.set_data(_h)
        return True

    @classmethod
    def check_ssh_alias(cls, _h):
        """Check for ssh alias"""

        log.debug("Checking ssh alias: '{0}'...".format(text_type(_h)))
        try:
#            client = paramiko.SSHClient()
#            client.load_system_host_keys()

            _cmd = ["ssh", "-o", "ConnectTimeout=1", _h, "exit 0"]
            subprocess.check_call(_cmd, stdout=open("/dev/null", 'w')) # , stderr=open("/dev/null", 'w')
            log.debug("Ssh alias '{0}' is functional!" . format(text_type(_h)))

            return True
        except subprocess.CalledProcessError as err:
            log.warning("Non-functional ssh alias: '{0}' => exit code: {1}!" . format(text_type(_h), err.returncode))
        except: # Any other exception is wrong...
            log.warning("Non-functional ssh alias: '{0}'. Moreover: Unexpected error: {1}" . format(text_type(_h), sys.exc_info()))

        return False

    @classmethod
    def parse(cls, d, parent=None):
        self = cls(parent)

        if d is None:
            d = self._default_data

        if self.validate(d):  # TODO: FIXME: NOTE: validate should not **explicitly** throw exceptions!!!
            return self  # .get_data()

        # NOTE: .parse should!
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data: '{}'!" .format(d)))

###############################################################
class HostMACAddress(BaseString):
    """MAC Address of the station"""

    def __init__(self, parent):
        BaseString.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid ssh alias?"""

        v = BaseString.parse(d, parent=self)

        if not re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", v.lower()):
            _value_error(None, d, d.lc, "ERROR: Wrong MAC Address: [{}]")
            return False

        # TODO: verify the existence of that MAC address?
        self.set_data(v)
        return True

###############################################################
class BaseBool(BaseScalar):
    def __init__(self, parent):
        BaseScalar.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid string"""

        if not isinstance(d, bool):
            print("ERROR: not a boolean value: '{}'" . format(d))
            return False

        self.set_data(d)
        return True


class StationVisibility(BaseBool):  ## "hidden": True / [False]
    def __init__(self, parent):
        BaseBool.__init__(self, parent)
        self._default_data = False


class AutoTurnon(BaseBool):  # Bool, False
    def __init__(self, parent):
        BaseBool.__init__(self, parent)
        self._default_data = False  # no powering on by default!?


###############################################################
class VariadicRecordWrapper(Base):
    """VariadicRecordWrapper record. Type is determined by the given 'type' field."""

    def __init__(self, parent):
        Base.__init__(self, parent)

        self._type_tag = text_type('type')
        self._type_cls = None

        self._default_type = None
        self._types = {}

    # TODO: FIXME: make sure to use this .parse instead of .validate due to substitution in Wrapper objects!!!

    @classmethod
    def parse(cls, d, parent=None):
        """Will return a Validator of a different class"""

        self = cls(parent)  # temporary wrapper object

        if d is None:
            d = self._default_data

        if self.validate(d):
            return self.get_data()

    def validate(self, d):
        """determine the type of variadic data for the format version"""

        _ret = True
        assert isinstance(d, dict)

        assert self._default_type is not None
        assert self._default_type in self._types

        _rule = self._types[self._default_type] # Version dependent!
        assert _rule is not None

        assert self._type_cls is not None

        if self._type_tag not in d:
            _lc = d.lc  # start of the current mapping
            _key_error(self._type_tag, d, _lc, "ERROR: Missing mandatory key `{}`")
            return False

        t = self._type_cls.parse(d[self._type_tag], parent=self.get_parent()) ### ????

        if t not in _rule:
            _lc = d.lc  # start of the current mapping
            _key_error(self._type_tag, t, _lc, "ERROR: unsupported/wrong variadic type: '{}'")
            return False

        tt = _rule[t](self)

        if not tt.validate(d):
            _lc = d.lc.key(self._type_tag)
            _value_error('*', d, _lc, "ERROR: invalid mapping value '{}' for type '%s'" % t)
            return False

        self.set_data(tt)  # TODO: completely replace this with tt??? access Methods?
        return True


###############################################################
class StationPowerOnMethodWrapper(VariadicRecordWrapper):
    """StationPowerOnMethod :: Wrapper"""

    def __init__(self, parent):
        VariadicRecordWrapper.__init__(self, parent)

        T = StationPowerOnMethodType
        self._type_cls = T
        _wol = {T.parse("WOL"): WOL, T.parse("DockerMachine"): DockerMachine}

        self._default_type = "default_WOL_poweron_method_wrapper"
        self._types[self._default_type] = _wol


###############################################################
class ServiceWrapper(VariadicRecordWrapper):
    """Service :: Wrapper"""

    def __init__(self, parent):
        VariadicRecordWrapper.__init__(self, parent)

        T = ServiceType
        self._type_cls = T
        _dc = {T.parse("compose"): DockerComposeService}

        self._default_type = "default_docker_compose_service_wrapper"
        self._types[self._default_type] = _dc


###############################################################
class ApplicationWrapper(ServiceWrapper):
    """Application :: Wrapper"""

    def __init__(self, parent):
        ServiceWrapper.__init__(self, parent)

        T = ServiceType # same for docker-compose Services and Applications!
        self._type_cls = T
        _dc = {T.parse("compose"): DockerComposeApplication}

        self._default_type = "default_docker_compose_application_wrapper"
        self._types[self._default_type] = _dc


###############################################################
class DockerMachine(BaseRecord):
    """DockerMachine :: StationPowerOnMethod"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._type_tag = text_type('type')

        self._default_type = 'DockerMachine'

        DM_rule = {
            self._type_tag: (True, StationPowerOnMethodType),  # Mandatory!
            text_type('auto_turnon'): (False, AutoTurnon),
            text_type('vm_name'): (True, BaseString),
            text_type('vm_host_address'): (True, HostAddress)
        }

        self._types = {self._default_type: DM_rule}  # ! NOTE: AMT - maybe later...


    def run_action(self, action, action_args):
        assert action == 'poweron'

        # process call: ssh to vm_host + docker-machione start vm_id
        raise NotImplementedError("Running 'docker-machine start' action is not supported yet... Sorry!")


class WOL(BaseRecord):
    """WOL :: StationPowerOnMethod"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._type_tag = text_type('type')
        self._default_type = 'WOL'

        WOL_rule = {
            self._type_tag: (True, StationPowerOnMethodType),  # Mandatory!
            text_type('auto_turnon'): (False, AutoTurnon),
            text_type('mac'): (True, HostMACAddress)
        }

        self._types = {self._default_type: WOL_rule}

    def run_action(self, action, action_args):
        assert action == 'poweron'

        # process call: wakeonlan + mac + IP address (get from parent's ssh alias!?)
        raise NotImplementedError("Running 'WOL' action is not supported yet... Sorry!")


###############################################################
class DockerComposeService(BaseRecord):
    """DockerCompose :: Service data type"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

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

    def validate(self, d):
        if not BaseRecord.validate(self, d):
            assert self.get_data() is None
            return False

        _d = self.get_data()

        # TODO: remove Validators (BaseString) from strings used as dict keys!
        _f = _d[self._file_tag]

        while isinstance(_f, Base):
            _f = _f.get_data()

        _n = _d[self._name_tag]
        while isinstance(_n, Base):
            _n = _n.get_data()

        if not os.path.exists(_f):  # TODO: FIXME: use URI::check() instead??
            if PEDANTIC:
                log.error("Missing file with docker-compose configuration: '%s'", _f)
                return False
            log.warning("Missing file with docker-compose configuration: '{0}'. Cannot check the service reference id: '{1}'" .format(_f, _n))
            return True


        # TODO: Check the corresponding file for such a service -> Service in DockerService!

        DC = "docker-compose"

        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
               _cmd = [DC, "-f", _f, "config"]  # TODO: use '--services'?
               try:
                   subprocess.check_call(_cmd, stdout=tmp, stderr=open("/dev/null", 'w'))
                   _ret = True
               except:
                   print("WARNING: error running '{}' to check '{}' (exit code: {})!".format(DC, _f, sys.exc_info()))
                   _ret = not PEDANTIC  # TODO: add a special switch?

            with open(path, 'r') as tmp:
                dc = load_yaml(tmp)  # NOTE: loading external Docker-Compose's YML file using our validating loader!
                ss = None
                for k in dc['services']:
                    if k == _n:
                        ss = dc['services'][k]
                        break

                if ss is None:
                    print("ERROR: missing service/application '{}' in file '{}' !".format(_n, _f))
                    _ret = False
        finally:
#            print(path)
            os.remove(path)

        return _ret


###############################################################
class DockerComposeApplication(DockerComposeService):
    """DockerCompose :: Application"""

    def __init__(self, parent):
        DockerComposeService.__init__(self, parent)

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
class Profile(BaseRecord):
    """Profile"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

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
class StationSSHOptions(BaseRecord):  # optional: "Station::ssh_options" # record: user, port, key, key_ref
    """StationSSHOptions"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._default_type = "default_station_ssh_options"

        default_rule = {
            text_type('user'): (False, BaseString),
            text_type('key'): (False, BaseString),
                text_type('port'): (False, BaseString),
        # TODO: BaseInt??  http://stackoverflow.com/questions/4187185/how-can-i-check-if-my-python-object-is-a-number
            text_type('key_ref'): (False, URI),
        }

        self._types = {self._default_type: default_rule}

    def validate(self, data):
        """check whether data is a valid ssh connection options"""

        _ret = BaseRecord.validate(self, data)

        # TODO: Check for ssh connection: Use some Python SSH Wrapper (2/3)
        return _ret


###############################################################
class Station(BaseRecord): # Wrapper
    """Station"""

    _extends_tag = text_type('extends')
    _client_settings_tag = text_type('client_settings')

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._poweron_tag = text_type('poweron_settings')
        self._ssh_options_tag = text_type('ssh_options')
        self._address_tag = text_type('address')
        self._ishidden_tag = text_type('hidden')

        self._default_type = "default_station"
        default_rule = {
            self._extends_tag: (False, StationID),
            text_type('name'): (True, BaseUIString),
            text_type('description'): (True, BaseUIString),
            text_type('icon'): (False, Icon),
            text_type('profile'): (True, ProfileID),
            self._address_tag: (True, HostAddress),
            self._poweron_tag: (False, StationPowerOnMethodWrapper),  # !! variadic, PowerOnType...
            self._ssh_options_tag: (False, StationSSHOptions),  # !!! record: user, port, key, key_ref
            text_type('omd_tag'): (True, StationOMDTag),  # ! like ServiceType: e.g. agent. Q: Is this mandatory?
            self._ishidden_tag: (False, StationVisibility),  # Q: Is this mandatory?
            self._client_settings_tag: (False, StationClientSettings)  # IDMap : (BaseID, BaseString)
        }  # text_type('type'): (False, StationType), # TODO: ASAP!!!

        self._types = {self._default_type: default_rule}

        self._compatible_applications = None  # TODO: FIXME!

    def is_hidden(self):
        _d = self.get_data()
        assert _d is not None

        _h = None

        if self._ishidden_tag in _d:
            _h = _d[self._ishidden_tag]
        else:
            _h = StationVisibility.parse(None, parent=self)

        return _h

    def get_address(self):
        _d = self.get_data()
        assert _d is not None

        _h = None

        if self._address_tag in _d:
            _h = _d[self._address_tag]
        else:
            _h = StationVisibility.parse(None, parent=self)

        return _h

    def shutdown(self, action_args):
        ### ssh address subprocess
        raise NotImplementedError("Cannot shutdown this station!")

    def deploy(self, action_args):
        ### see existing deploy.sh!?
        raise NotImplementedError("Cannot deploy local configuration to this station!")

    def start_service(self, action_args):
        raise NotImplementedError("Cannot start a service/application on this station!")

    def finish_service(self, action_args):
        raise NotImplementedError("Cannot finish a service/application on this station!")

    def app_switch(self, action_args):
        raise NotImplementedError("Cannot switch an application on this station!")

    def poweron(self, action_args):
        _d = self.get_data()
        assert _d is not None

        if not self._poweron_tag in _d:
            log.error("Cannot Power-On this station since the corresponding method is missing!")
            raise NotImplementedError("Cannot Power-On this station!")

        poweron = _d[self._poweron_tag]
        if poweron is None:
            log.error("Cannot Power-On this station since the corresponding method was not specified properly!")
            raise NotImplementedError("Cannot Power-On this station!")

        poweron.run_action('poweron', action_args)  # ????

    def run_action(self, action, action_args):
        """
        Run the given action on/with this station

        :param action_args: arguments to the action
        :param action:
                poweron <StationID> [<args>]
                shutdown <StationID> [<args>]
                deploy <StationID> [<args>]
                start <StationID> [<ServiceID/ApplicationID>]
                finish <StationID> [<ServiceID/ApplicationID>]
                app_switch <StationID> <new ApplicationID>

        :return: nothing.
        """

        if action == 'poweron':
            self.poweron(action_args)
        elif action == 'shutdown':
            self.shutdown(action_args)
        elif action == 'deploy':
            self.deploy(action_args)
        elif action == 'start':
            self.start_service(action_args)
        elif action == 'finish':
            self.finish_service(action_args)
        elif action == 'app_switch':
            self.app_switch(action_args)

        # Run 'ssh address hilbert-station action action_args'?!
        raise NotImplementedError("Running action '{0} {1}' is not supported yet... Sorry!" . format(action, action_args))


    def get_base(self):
        _d = self.get_data()
        assert _d is not None
        _b = _d.get(self._extends_tag, None)  # StationID (validated...)

#        if _b is not None:
#            if isinstance(_b, Base):
#                _b = _b.get_data()

        return _b

    def extend(delta, base):  # delta == self!
        assert delta.get_base() is not None
        assert base.get_base() is None

        # NOTE: at early stage there may be no parent data...
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
                dd = StationClientSettings.parse(None, parent=delta.get_parent())

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
class BaseIDMap(Base):
    """Mapping: SomeTypeID -> AnyType"""

    def __init__(self, parent):
        Base.__init__(self, parent)
        self._default_type = None
        self._types = {}  # type -> (TypeID, Type)

    def detect_type(self, d):
        """determine the type of variadic data for the format version"""

        assert not (self._default_type is None)
        assert len(self._types) > 0

        return self._default_type

    def validate(self, d):
        assert isinstance(d, dict)

        self._type = self.detect_type(d)

        assert self._type is not None
        assert self._type in self._types

        (_id_rule, _rule) = self._types[self._type]

        _lc = d.lc  # starting position?
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
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_services"
        self._types = {self._default_type: (ServiceID, ServiceWrapper)}

        # def validate(self, data):
        #     _ret = BaseID.validate(self, data)
        #     ### TODO: Any post processing?
        #     return _ret


###############################################################
# "client_settings": (False, StationClientSettings) # IDMap : (BaseID, BaseString)
class StationClientSettings(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_station_client_settings"
        self._types = {
            self._default_type: (ClientVariable, BaseScalar)
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
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_applications"
        self._types = {self._default_type: (ApplicationID, ApplicationWrapper)}

###############################################################
class GlobalProfiles(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_profiles"
        self._types = {self._default_type: (ProfileID, Profile)}

        # def validate(self, data):
        #     _ret = BaseID.validate(self, data)
        #     ### TODO: Any post processing?
        #     return _ret


###############################################################
class GlobalStations(BaseIDMap):
    """Global mapping of station IDs to Station's"""

    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_stations"
        self._types = {self._default_type: (StationID, Station)}  # NOTE: {StationID -> Station}

    def validate(self, d):
        """Extension mechanism on top of the usual ID Mapping parsing"""

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

        return _ret


###############################################################
class BaseList(Base):
    """List of entities of the same type"""

    def __init__(self, parent):
        Base.__init__(self, parent)

        self._default_type = None
        self._types = {}

    def validate(self, d):
        assert self._default_type is not None
        assert len(self._types) > 0

        _lc = d.lc

        # NOTE: determine the class of items based on the version and sample data
        self._type = self._types[self._default_type]
        assert self._type is not None

        if (not isinstance(d, (list, dict, tuple, set))) and isinstance(d, string_types):
            try:
                _d = [self._type.parse(BaseString.parse(d, parent=self))]
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

    def __init__(self, parent):
        BaseList.__init__(self, parent)

        self._default_type = "default_GroupID_list"
        self._types = {self._default_type: GroupID}


###############################################################
class ServiceList(BaseList):
    """List of ServiceIDs or a single ServiceID!"""

    def __init__(self, parent):
        BaseList.__init__(self, parent)

        self._default_type = "default_ServiceID_list"
        self._types = {self._default_type: ServiceID}


###############################################################
class ServiceTypeList(BaseList):
    """List of ServiceType's or a single ServiceType!"""

    def __init__(self, parent):
        BaseList.__init__(self, parent)

        self._default_type = "default_ServiceType_list"
        self._types = {self._default_type: ServiceType}


###############################################################
class Group(BaseRecord):  # ? TODO: GroupSet & its .parent?
    """Group"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

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
            return GroupID, BaseScalar

        return None

    def validate(self, d):
        _ret = BaseRecord.validate(self, d)

        # TODO: FIXME: Add extra keys into include!

        return _ret



###############################################################
class GlobalGroups(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_groups"
        self._types = {self._default_type: (GroupID, Group)}


###############################################################
class Preset(BaseRecord):
    """Preset"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

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
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_presets"
        self._types = {self._default_type: (PresetID, Preset)}

    def validate(self, data):
        print("WARNING: Presets are not supported yet!")
        #        raise NotImplementedError("Presets are not supported yet!")
        return True

###############################################################
class Hilbert(BaseRecord):
    """General Hilbert Configuration format"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)  # This is the Main Root!

        self._default_type = "default_global"

        self._version_tag = text_type('Version')
        self._applications_tag = text_type('Applications')
        self._services_tag = text_type('Services')
        self._profiles_tag = text_type('Profiles')
        self._stations_tag = text_type('Stations')
        self._groups_tag = text_type('Groups')

        ### explicit (optional) Type?
        default_rule = {
            self._version_tag: (True, SemanticVersion),  # Mandatory, specifies supported Types of Config's Entity
            self._services_tag: (True, GlobalServices),
            self._applications_tag: (True, GlobalApplications),
            self._profiles_tag: (True, GlobalProfiles),
            self._stations_tag: (True, GlobalStations),
            self._groups_tag: (False, GlobalGroups),  # Optional
            text_type('Presets'): (False, GlobalPresets),  # Optional. May be removed! default?
        }

        self._types = {self._default_type: default_rule}

        self._default_data = None

    @classmethod
    def parse(cls, d, parent=None):
        self = cls(parent)

        if d is None:
            d = self._default_data

        if self._version_tag not in d:
            _key_note(self._version_tag, d.lc, "ERROR: Missing mandatory '{}' key field!")
            raise ConfigurationError(u"{}: {}".format("ERROR:", "Missing version tag '{0}' in the input: '{1}'!".format(self._version_tag, d)))

        try:
            _v = SemanticVersion.parse(d[self._version_tag], parent=self, partial=True)
        except:
            _value_error(self._version_tag, d, d.lc, "Wrong value of global '{}' specification!")
            raise

        self.set_version(_v)  # NOTE: globally available now!

        if self.validate(d):
            return self.get_data()

        return None

    def validate(self, data):
        _ret = BaseRecord.validate(self, data)

        for offset, k in enumerate(data):
            if k == self._version_tag:
                if offset != 0:
                    print("Note: '{}' specified correctly but not ahead of everything else (offset: {})!".format(
                        self._version_tag, offset))
                    _ret = False
                break

        # NOTE: check uniqueness of keys among (Services/Applications):
        _services = data.get(self._services_tag)  # Rely on the above and use get_data?
        _applications = data.get(self._applications_tag)

        for p, k in enumerate(_services):
            _lc = _services.lc.key(k)

            if k in _applications:
                print("Error: '{}' is both a ServiceID and an ApplicationID:".format(k))
                _key_error(k, _services[k], _lc, "Service key: {}")

                _alc = _applications.lc.key(k)
                _key_error(k, _applications[k], _alc, "Application key: {}")

        # ! TODO: check Uniqueness of keys among (Profiles/Stations/Groups) !!!!
        # ! TODO: check for GroupID <-> StationID <-> ProfileID
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

    cfg = Hilbert(parent)
    if not cfg.validate(d):
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Cannot parse given configuration!"))
    
    return cfg
#    return Hilbert.parse(d, parent=parent)


###############################################################
def yaml_dump(d, stream=None):
    return yaml.round_trip_dump(d, stream=stream)
