# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import logging
# log = logging.getLogger(__name__)

PEDANTIC = False  # NOTE: to treat invalid values/keys as errors?
INPUT_DIRNAME = './'
OUTPUT_DIRNAME = INPUT_DIRNAME

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
            print("Unexpected error: ", sys.exc_info()[0])
            print("Cannot get line out of: ", lc)
            raise

        try:
            c = lc.col
        except:
            try:
                c = lc.column
            except:
                print("Unexpected error: ", sys.exc_info()[0])
                print("Cannot get col/column out of: ", lc)
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
        key = '*'

    print('{}[line: {}, column: {}]: {}'.format(e, line + 1, col + 1, key_message.format(key)))
    print('---')


def _value_error(key, value, lc, error, e='E'):
    (line, col) = _get_line_col(lc)

    if key is None:
        key = '*'

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
def load_yaml(f, Loader=VerboseRoundTripLoader, version=(1, 2), preserve_quotes=True):
    try:
        return yaml.load(f, Loader=Loader, version=version, preserve_quotes=preserve_quotes)
    except (IOError, yaml.YAMLError) as e:
        error_name = getattr(e, '__module__', '') + '.' + e.__class__.__name__
        raise ConfigurationError(u"{}: {}".format(error_name, e))


###############################################################
from ruamel.yaml.compat import PY2, PY3, text_type, string_types
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

    def __init__(self, parent): # TODO: add tag? here or in some child?
        AbstractValidator.__init__(self)
        assert self._parent is None
        self._parent = parent

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
        if self._data is None:
            return self._default_data

        return self._data

    @classmethod
    def parse(cls, d, parent=None):
        self = cls(parent)

#        print(cls)
#        print(parent)
#        print(self)
#        print(d)

        if self.validate(d):  # TODO: FIXME: NOTE: validate should not **explicitly** throw exceptions!!!
            return self.get_data()

        # NOTE: .parse should!
        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data: '{}'!" .format(d)))


###############################################################
class BaseRecord(Base):
    """Aggregation of data as a record with some fixed data memebers"""

    # TODO: turn _default_type into a class-member (by moving it here)...?

    def __init__(self, parent):
        Base.__init__(self, parent)
        self._default_type = None  # "default_base"
        self._types = {}
        self._create_optional = False


    def detect_type(self, d):
        """determine the type of variadic data for the format version"""

        assert not (self._default_type is None)
        assert len(self._types) > 0

        return self._default_type

    def detect_extra_rule(self, key, value):  # Any extra unlisted keys in the mapping?
        return None

    def validate(self, d):
        # ! TODO: assert that d is a mapping with lc!

        _type = self.detect_type(d)

        assert not (_type is None)
        assert _type in self._types

        _rule = self._types[_type]

        _ret = True

        _lc = d.lc  # starting location of the mapping...?
        (s, c) = (_lc.line, _lc.col)

        _d = {}

        for k in _rule.keys():
            r = _rule[k]
            if r[0] and (k not in d):
                _key_note(k, _lc, "ERROR: Missing mandatory key `{}` (type: '%s')" % (_type))  # Raise Exception?
                _ret = False
            # NOTE: the following will add all the missing default values
            elif (not r[0]) and self._create_optional:  # Optional Values should have some default values!
                _d[k] = r[1](self).get_data()  # NOTE: default value - no validation

        for offset, k in enumerate(d):
            v = d.get(k)
            l = s + offset  # ??
            lc = (l, c)

            if k in _rule:
                r = _rule[k][1](self)

                if not r.validate(v):  # TODO: save to self!
                    _value_error(k, v, lc, "Error: invalid field '{}' value (type: '%s')" % _type)
                    _ret = False

                _d[k] = r.get_data()
            else:
                _extra_rule = self.detect_extra_rule(k, v)  # (KeyValidator, ValueValidator)

                if _extra_rule is None:
                    _key_error(k, v, lc, "WARNING: Unhandled extra Key: '{}' (type: '%s')" % _type)
                    _ret = False
                else:
                    _k = _extra_rule[0](self)

                    if not _k.validate(k):
                        _key_error(k, v, lc, "Error: invalid key '{}' (type: '%s')" % _type)
                        _ret = False
                    else:
                        _v = _extra_rule[1](self)
                        if not _v.validate(v):  # TODO: FIXME: wrong col (it was for key - not value)!
                            _value_error(k, v, lc, "Error: invalid field value '{}' value (type: '%s')" % _type)
                            _ret = False
                        else:
                            _d[_k.get_data()] = _v.get_data()

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

        if isinstance(d, (list, dict, tuple, set)): # ! Check if data is not a container?
            print("ERROR: value: '{}' is not a scalar value!!" . format(d))
            return False

        self.set_data(d)
        return True


###############################################################
class BaseString(BaseScalar):
    """YAML String"""
    def __init__(self, parent):
        BaseScalar.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid string. Note: should not care about format version"""

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
    def __init__(self, parent):
        BaseString.__init__(self, parent)

    def validate(self, d):
        """check the string data to be a valid semantic verions"""

        _t = BaseString.parse(d, parent=self)

        _v = self.get_version(None)
        try:
#            if _v is None:  # NOTE: the only initial validation: may be a partial version
#                _v = semantic_version.Version(_t, partial=True)  # TODO: check this!
#            else:
            _v = semantic_version.Version.parse(_t, partial=True, coerce=True)
        except:
            print("ERROR: wrong version data: '{0}' (see: '{1}')" . format(d, sys.exc_info()))
            return False

        self.set_data(_v)
        return True


###############################################################
class BaseUIString(BaseString):  # visible to user => non empty!
    def __init__(self, parent):
        BaseString.__init__(self, parent)

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
class ServiceType(BaseEnum):  ## Q: Is 'Service::type' mandatory? default: 'compose'
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)

        compose = 'compose'
        self._enum_list = [compose] # NOTE: 'docker' and others may be possible later on
        self._default_data = compose


###############################################################
class StationOMDTag(BaseEnum):  ## Q: Is 'Station::omd_tag' mandatory? default: 'standalone'
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)

        _v = 'standalone'
        self._enum_list = ['agent', 'windows', _v]  # possible values of omd_tag # will depend on format version!
        self._default_data = _v


###############################################################
class StationPowerOnMethodType(BaseEnum):  # Enum: [WOL], AMTvPRO, DockerMachine
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)

        wol = 'WOL'
        # NOTE: the list of possible values of PowerOnMethod::type (will depend on format version)
        self._enum_list = [wol, 'DockerMachine']  # NOTE: 'AMTvPRO' and others may be possible later on
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

        if urlparse(v).scheme != "":
            self._type = "url"
            try:
                urlopen(v).close()
            except:
                print("WARNING: URL: '{}' is not accessible!".format(v))
                _ret = not PEDANTIC

        # TODO: FIXME: base location should be the input file's dirname???
#        elif not os.path.isabs(v):
#            v = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), v))

        elif os.path.isfile(v):  # Check whether file exists
            self._type = "file"

        elif os.path.isdir(v):  # Check whether directory exists
            self._type = "dir"

        if not _ret:
            print("WARNING: missing/unsupported resource location: {}".format(v))
            _ret = (not PEDANTIC)

        if _ret:
            self.set_data(v)

        return _ret

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

        v = BaseID.parse(d, parent=self)

        _ret = True

        if not (v == v.lower() or v == v.upper()):  # ! Variables are all lower or upper case!
            print("ERROR: a variable must be either in lower or upper case! Input: '{}'" . format(d))
            _ret = False

        # NOTE: starting with hilbert_ or HILBERT_ with letters, digits and '_'??
        if not re.match("^hilbert(_[a-z0-9]+)+$", v.lower()):
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
        script = BaseString.parse(d, parent=self)

        # NOTE: trying to check the BASH script: shellcheck & bash -n 'string':
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
#                print(script)
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
        self._default_data = "docker-compose.yml"

    def validate(self, d):
        """check whether data is a valid docker-compose file name"""
        ref = URI.parse(d, parent=self)
        self.set_data(ref)
        return True

    # TODO: call docker-compose on the referenced file! in DockerService!


###############################################################
class Icon(URI):
    def __init__(self, parent):
        URI.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid icon file name"""
        ref = URI.parse(d, parent=self)

        # TODO: check the file contents (or extention)

        self.set_data(ref)
        return True


###############################################################
import subprocess # , shlex

class HostAddress(BaseString):
    """SSH alias"""

    def __init__(self, parent):
        BaseString.__init__(self, parent)

    def validate(self, d):
        """check whether data is a valid ssh alias?"""

        _h = BaseString.parse(d, parent=self)

        _cmd = ["ssh", "-o", "ConnectTimeout=2", _h, "exit 0"]
        try:
            # NOTE: Check for ssh alias!
            subprocess.check_call(_cmd, stdout=open("/dev/null", 'w'), stderr=open("/dev/null", 'w'))
            _ret = True
        except subprocess.CalledProcessError as err:
            print("WARNING: non-functional ssh alias: '{0}' => exit code: {1}!" . format(text_type(_h), err.returncode))
            _ret = not PEDANTIC # TODO: add a special switch?
        except: # Any other exception is wrong...
            print("WARNING: non-functional ssh alias: '{0}'. Moreover: Unexpected error: {1}" . format(text_type(_h), sys.exc_info()))
            _ret = not PEDANTIC  # TODO: add a special switch?

        if _ret:
            self.set_data(_h)

        return _ret

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
        ### TODO: Detect other YAML scalar types?

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

        self._type_tag = "type"
        self._type_cls = None

        self._default_type = None
        self._types = {}

    def validate(self, d):
        """determine the type of variadic data for the format version"""

        _ret = True

        assert self._default_type is not None
        assert self._default_type in self._types

        _rule = self._types[self._default_type] # Version dependent!
        assert _rule is not None

        assert self._type_cls is not None

        if self._type_tag not in d:
            _lc = d.lc  # start of the current mapping
            _key_error(self._type_tag, d, _lc, "ERROR: Missing mandatory key `{}`")
            return False

        t = self._type_cls.parse(d[self._type_tag], parent=self)

        if t not in _rule:
            _lc = d.lc  # start of the current mapping
            _key_error(self._type_tag, t, _lc, "ERROR: unsupported/wrong variadic type: '{}'")
            return False

        tt = _rule[t](self)

        if not tt.validate(d):
            _lc = d.lc.key(self._type_tag)
            _value_error('*', d, _lc, "ERROR: invalid mapping value '{}' for type '%s'" % t)
            return False

        self.set_data(tt.get_data())
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

        self._type_tag = "type"

        self._default_type = "DockerMachine"

        DM_rule = {
            self._type_tag: (True, StationPowerOnMethodType),  # Mandatory!
            "auto_turnon": (False, AutoTurnon),
            "vm_name": (True, BaseString),
            "vm_host_address": (True, HostAddress)
        }

        self._types = {self._default_type: DM_rule}  # ! NOTE: AMT - maybe later...

class WOL(BaseRecord):
    """WOL :: StationPowerOnMethod"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._type_tag = "type"
        self._default_type = "WOL"

        WOL_rule = {
            self._type_tag: (True, StationPowerOnMethodType),  # Mandatory!
            "auto_turnon": (False, AutoTurnon),
            "mac": (True, HostMACAddress)
        }

        self._types = {self._default_type: WOL_rule}


###############################################################
class DockerComposeService(BaseRecord):
    """DockerCompose :: Service data type"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._type_tag = "type"
        self._hook_tag = "auto_detections"
        self._name_tag = "ref"
        self._file_tag = "file"

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

        _f = _d[self._file_tag]

        assert os.path.exists(_f)

        _n = _d[self._name_tag]
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
                dc = load_yaml(tmp)
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
            "name": (True, BaseUIString),  # NOTE: name for UI!
            "description": (True, BaseUIString),
            "icon": (False, Icon),
            "compatibleStations": (True, Group)
        })

        self._types[self._default_type] = _compose_rule


###############################################################
class Profile(BaseRecord):
    """Profile"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._default_type = "default_profile"

        default_rule = {
            "name": (True, BaseUIString),
            "description": (True, BaseUIString),
            "icon": (False, Icon),
            "services": (True, ServiceList),
            "supported_types": (False, ServiceTypeList)
        }

        self._types = {self._default_type: default_rule}


###############################################################
class StationSSHOptions(BaseRecord):  # optional: "Station::ssh_options" # record: user, port, key, key_ref
    """StationSSHOptions"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._default_type = "default_station_ssh_options"

        default_rule = {
            "user": (False, BaseString),
            "key": (False, BaseString),
            "port": (False, BaseString),
        # TODO: BaseInt??  http://stackoverflow.com/questions/4187185/how-can-i-check-if-my-python-object-is-a-number
            "key_ref": (False, URI),
        }

        self._types = {self._default_type: default_rule}

    def validate(self, data):
        """check whether data is a valid ssh connection options"""

        _ret = BaseRecord.validate(self, data)

        # TODO: Check for ssh connection: Use some Python SSH Wrapper (2/3)
        return _ret


###############################################################
class Station(BaseRecord):
    """Station"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._default_type = "default_station"

        default_rule = {
            "name": (True, BaseUIString),
            "description": (True, BaseUIString),
            "icon": (False, Icon),
            "extends": (False, StationID),
            "profile": (True, ProfileID),
            "address": (True, HostAddress),
            "poweron_settings": (False, StationPowerOnMethodWrapper),  # !! variadic, PowerOnType...
            "ssh_options": (False, StationSSHOptions),  # !!! record: user, port, key, key_ref
            "omd_tag": (True, StationOMDTag),  # ! like ServiceType: e.g. agent. Q: Is this mandatory?
            "hidden": (False, StationVisibility),  # Q: Is this mandatory?
            "client_settings": (False, StationClientSettings)  # IDMap : (BaseID, BaseString)
        }

        self._types = {self._default_type: default_rule}


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

    def validate(self, data):
        _type = self.detect_type(data)

        assert not (_type is None)
        assert _type in self._types

        (_id, _rule) = self._types[_type]

        _ret = True

        _lc = data.lc  # starting position?
        (s, c) = (_lc.line, _lc.col)

        _d = {}
        for offset, k in enumerate(data):
            v = data.get(k)  # TODO: data[offset]???
            l = s + offset
            _lc = (l, c)

            id = _id(self)

            if not id.validate(k):
                _key_error(k, v, _lc, "Invalid Key ID: '{}' (type: '%s')" % (_type))  # Raise Exception?
                _ret = False
            else:
                vv = _rule(self)

                if not vv.validate(v):
                    _value_error(k, v, _lc, "invalid value '{}' value (type: '%s')" % (_type))  # Raise Exception?
                    _ret = False
                elif _ret:
                    _d[id.get_data()] = vv.get_data()

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
class StationClientSettings(
    BaseIDMap):  # "client_settings": (False, StationClientSettings) # IDMap : (BaseID, BaseString)
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_station_client_settings"
        self._types = {
            self._default_type: (ClientVariable, BaseScalar)}  # ! TODO: only strings for now! More scalar types?!


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

def extend_dict(base, delta, _ext):
    new = {}

    for k in base:
        if k == _ext:
            continue

        if k in delta:
            v = delta.get(k, None)

            if v is None:
                new[k] = base[k]
                continue

            if k == 'client_settings':
                t = base.get(k, {}).copy()

                assert isinstance(t, dict)
                assert isinstance(v, dict)

                t.update(v)
                new[k] = t
            else:
                new[k] = v  # overwrite the rest
        else:
            new[k] = base[k]


    for k in delta:
        if not ((k == _ext) or (k in new)):
            new[k] = delta[k]

    return new

###############################################################
class GlobalStations(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_stations"
        self._types = {self._default_type: (StationID, Station)}

    def validate(self, d):
        """Extension mechanism on top of the usual ID Mapping parsing"""

        if not BaseIDMap.validate(self, d):
            return False

        _ext = 'extends'

        sts = self.get_data()
        self.set_data(None)

        _ret = True

        _processed = {}
        _todo = {}
        for k in sts:
            v = sts[k]
            if v.get(_ext, None) is None:
                _processed[k] = v
            else:
                _todo[k] = v

        _chg = True
        while bool(_todo) and _chg:
            _chg = False
            _rest = {}
            while bool(_todo):
                k, v = _todo.popitem()
                assert _ext in v
                base = v[_ext]
                if base in _processed:
                    _processed[k] = extend_dict(_processed[base], v, _ext)
                    _chg = True
                else:
                    _rest[k] = v
            _todo = _rest

        if bool(_todo):
            print('ERROR: Cyclic dependencies between stations: {}!?' .format(_todo))
            _ret = False

        if _ret:
            self.set_data(_processed)

        return _ret


###############################################################
class BaseList(Base):
    """List of entities of the same type"""

    def __init__(self, parent):
        Base.__init__(self, parent)

    def validate(self, d):
        assert self._default_type is not None
        assert len(self._types) > 0

        # NOTE: determine the class of items based on the version and sample data
        _type = self._types[self._default_type]
        assert _type is not None

        if (not isinstance(d, (list, dict, tuple, set))) and isinstance(d, string_types):
            try:
                _d = _type.parse(BaseString.parse(d, parent=self), parent=self)
                self.get_data(_d)
                return True
            except:
                pass  # Not a single string entry...

        # list!?
        _d = []
        _ret = True

        for idx, i in enumerate(d):  # What about a string?
            _v = _type(self)
            if not _v.validate(i):
                _lc = d.lc
                _value_error("[%d]" % idx, d, _lc, "Wrong item in the given sequence!")
                _ret = False
            else:
                _d.insert(idx, _v.get_data())  # append?

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

        self._include_tag = "include"
        self._exclude_tag = "exclude"
        self._intersectWith_tag = "intersectWith"

        default_rule = {
            self._include_tag: (False, GroupIDList),
            self._exclude_tag: (False, GroupIDList),
            self._intersectWith_tag: (False, GroupIDList),
            "name": (False, BaseUIString),
            "description": (False, BaseUIString),
            "icon": (False, Icon)
        }

        self._types = {self._default_type: default_rule}

    def detect_extra_rule(self, key, value):  # Any extra unlisted keys in the mapping?
        if value is None:  # Set item!
            return (GroupID, BaseScalar)
        return None

    def validate(self, data):
        _ret = BaseRecord.validate(self, data)
        # Add extra keys into include?
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
class Global(BaseRecord):
    """General Hilbert Configuration format"""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)  # This is the Main Root!

        self._default_type = "default_global"

        self._version_tag = "Version"
        self._applications_tag = "Applications"
        self._services_tag = "Services"
        self._profiles_tag = "Profiles"
        self._stations_tag = "Stations"
        self._groups_tag = "Groups"

        ### explicit (optional) Type?
        default_rule = {
            self._version_tag: (True, SemanticVersion),  # Mandatory, specifies supported Types of Config's Entity
            self._services_tag: (True, GlobalServices),
            self._applications_tag: (True, GlobalApplications),
            self._profiles_tag: (True, GlobalProfiles),
            self._stations_tag: (True, GlobalStations),
            self._groups_tag: (False, GlobalGroups),  # Optional
            "Presets": (False, GlobalPresets),  # Optional. May be removed! default?
        }

        self._types = {self._default_type: default_rule}

        self._default_data = None

    @classmethod
    def parse(cls, d, parent=None):
        self = cls(parent)

        if self._version_tag not in d:
            _key_note(self._version_tag, d.lc, "ERROR: Missing mandatory '{}' key field!")
            raise ConfigurationError(u"{}: {}".format("ERROR:", "Missing version tag '{0}' in the input: '{1}'!".format(self._version_tag, d)))

        try:
            _v = SemanticVersion.parse(d[self._version_tag], parent=self)
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
def load_yaml_file(filename):
    with open(filename, 'r') as fh:
        return load_yaml(fh)

# class Hilbert(object):

def yaml_dump(d, stream=None):
    print(yaml.round_trip_dump(d, stream=stream))

def parse(d, parent=None):
    return Global.parse(d, parent=parent)

