#! /usr/bin/env python3
# coding: utf-8
# encoding: utf-8

from sys import argv, version_info

###############################################################
up_arrow = '↑'

def key_error(key, value, line, col, error_message, e='K'):
    print('{}[line: {}, column: {}]: {}'.format(e, line+1, col+1, error_message.format(key)))
    print('{}{}: {}'.format(' '*col, key, value))
    print('{}{}'.format(' '*(col), up_arrow))
    print('---')


def key_note(key, line, col, key_message, e='K'):
    print('{}[line: {}, column: {}]: {}'.format(e, line+1, col+1, key_message.format(key)))
    print('---')
                
    
def value_error(key, value, line, col, error, e='E'):
    val_col = col + len(key) + 2
    print('{}[line: {}, column: {}]: {}'.format(e, line+1, val_col+1, error . format(key)))
    print('{}{}: {}'.format(' '*col, key, value))
    print('{}{}'.format(' '*(val_col), up_arrow))
    print('---')

def value_warning(key, value, line, col, error):
    value_error(key, value, line, col, error, e='W')
    
###############################################################
import collections
import ruamel.yaml as yaml

from ruamel.yaml.reader import Reader
from ruamel.yaml.scanner import RoundTripScanner # Scanner
from ruamel.yaml.parser import RoundTripParser # Parser, 
from ruamel.yaml.composer import Composer
from ruamel.yaml.constructor import RoundTripConstructor # Constructor, SafeConstructor, 
from ruamel.yaml.resolver import VersionedResolver # Resolver, 
from ruamel.yaml.nodes import MappingNode

###############################################################
class VerboseRoundTripConstructor(RoundTripConstructor):
    def construct_mapping(self, node, deep=False):
        
        m = RoundTripConstructor.construct_mapping(self, node, deep) # the actual construction!

        # additionally go through all nodes in the mapping to detect overwrites:
        
        starts = {} # already processed keys + locations and values
        
        for key_node, value_node in node.value:
            # keys can be list -> deep
            key = self.construct_object(key_node, deep=True)
            
            # lists are not hashable, but tuples are
            if not isinstance(key, collections.Hashable):
                if isinstance(key, list):
                    key = tuple(key)

            value = self.construct_object(value_node, deep=deep)
            # TODO: check the lines above in the original Constructor.construct_mapping code for any changes/updates
            
            if key in starts: # Duplication detection
                old = starts[key]
                print( "WARNING: Key re-definition within some mapping: " ) # mapping details?
                key_error( key, old[1], old[0].line, old[0].column, "Previous Value: " )
                key_error( key, value, key_node.start_mark.line, key_node.start_mark.column, "New Value: ")
                print('===')
                
            starts[key] = (key_node.start_mark, value) # in order to find all such problems!
            
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
class ConfigurationError(Exception):
    def __init__(self, msg):
        self._msg = msg
        
###############################################################
def load_yaml(filename):
    try:
        with open(filename, 'r') as fh:
            return yaml.load(fh, Loader = VerboseRoundTripLoader, version = (1, 2), preserve_quotes=True)
        
    except (IOError, yaml.YAMLError) as e:
        error_name = getattr(e, '__module__', '') + '.' + e.__class__.__name__
        raise ConfigurationError(u"{}: {}".format(error_name, e))
    
###############################################################
from ruamel.yaml.compat import PY2, PY3, text_type
from abc import *

if PY3 and (version_info[1] >= 4):
    class Abstract(ABC):
        """Abstract Base class for any concrete implementation of entities appearing in the general configuration file"""
        @abstractmethod
        def validate(self, data):
            pass
elif PY2 or PY3:
    class Abstract:
        """Abstract Base class for any concrete implementation of entities appearing in the general configuration file"""
        __metaclass__ = ABCMeta
        @abstractmethod
        def validate(self, data):
            pass
#elif PY3:
#    class Abstract(metaclass=ABCMeta):
#        """Abstract Base class for any concrete implementation of entities appearing in the general configuration file"""
#        @abstractmethod
#        def validate(self, data):
#            pass
else:
    raise NotImplementedError("Unsupported Python version: '{}'".format(version_info))
    
###############################################################
class Base(Abstract):
    """Actual Base Class for the Config entities"""

    __version = [None]
    _data = None
    _parent = None

    def __init__(self, parent):
        Abstract.__init__(self)
        assert self._parent is None
        self._parent = parent
    
    def set_version(self, v):
        """To be set once only!"""
        assert len(self.__version) == 1
        assert self.__version[0] is None
        self.__version[0] = v

    def get_version(self):
        assert len(self.__version) == 1
        assert self.__version[0] is not None
        return  self.__version[0]
        
    def set_data(self, d):
        assert self._data is None
        self._data = d       

    def get_data(self):
        if self._data is None:
            return self._default_data
        
        return self._data
        
    @abstractmethod
    def validate(self, version, data): # version = None?
        pass

    def validate(self, data):
        return self.validate(self.get_version(), data)


    @classmethod
    def parse(cls, data, parent=None):
        self = cls(parent)
        
        if self.validate(get_version(), data):
            return self.get_data()

        raise ConfigurationError(u"{}: {}".format("ERROR:", "Invalid data!"))
        
        
    
###############################################################
class BaseRecord(Base):
    """Aggregation of data as a record with some fixed data memebers"""
        
    # TODO: turn _default_type into a class-member (by moving it here)...?
    
    def __init__(self, parent):
        Base.__init__(self, parent)        
        self._default_type = None # "default_base"
        self._types = {}


    def detect_type(self, data):
        return self.detect_type(self.get_version(), data)
    
#    @abstractmethod
#    def detect_type(self, version, data):
#        pass
    
        
    def detect_type(self, version, data):
        """determine the type of variadic data for the format version"""
        
        assert not (self._default_type is None)
        assert len(self._types) > 0        
        
        return self._default_type
    
    def detect_extra_rule(self, version, key, value): # Any extra unlisted keys in the mapping?
        return None

    def validate(self, version, data):
        #! TODO: assert that data is a mapping with lc!
        
        _type = self.detect_type(version, data)
        
        assert not (_type is None)
        assert _type in self._types
        
        _rule  = self._types[_type]

        _ret = True

        _lc = data.lc # starting location of the mapping...?
        (s, c) = (_lc.line, _lc.col)

        _d = {}
        
        for k in _rule.keys():
            r = _rule[k]
            if r[0] and (k not in data):
                key_note(k, s, c, "Error: Missing key `{}` (type: '%s')" % (_type)) # Raise Exception?
                _ret = False
            elif not r[0]: # Optional Values should have some default values!
                _d[k] = r[1](self) 
                

        for offset, k in enumerate(data):
            v = data.get(k)
            l = s + offset #??
            
            if k in _rule:
                r = _rule[k]
                
                _d[k] = r[1](self)
                
                if not _d[k].validate(version, v): # TODO: save to self!
                    value_error(k, v, l, c, "Error: invalid field '{}' value (type: '%s')" % (_type)) # Raise Exception?
                    _ret = False
            else:
                _key_rule = self.detect_extra_rule(version, k, v)

                if _key_rule is None:
                    key_error(k, v, l, c, "Error: Unhandled Key: '{}' (type: '%s')" % (_type)) # Raise Exception?
                    _ret = False
                else:                    
                    _d[k] = _key_rule(self)
                    
                    if not _d[k].validate(version, v): # TODO: save to self!
                        value_error(k, v, l, c, "Error: invalid field '{}' value (type: '%s')" % (_type)) # Raise Exception?
                        _ret = False
                        
        self.set_data(_d)

        return _ret    
    
###############################################################
class BaseScalar(Base):
    """Single scalar value out of YAML scalars: strings, numbert etc."""
    
    def __init__(self, parent):
        Base.__init__(self, parent)

    def validate(self, version, data):
        """check that data is a scalar: not a sequence of mapping"""

        _ret = True
#        #! NOTE: test that data is non-iterable! TODO: BUG: strings are iterable :(
#        try:
#            for x in data:
#                break
#            _ret = False
#        except:
#            _ret = True
            
        self.set_data( data )
        
        return _ret
        
###############################################################
#import semver
import semantic_version # supports partial versions
    
class SemanticVersion(BaseScalar):
    def __init__(self, parent):
        BaseScalar.__init__(self, parent)
        
    def validate(self, version, data):
        """check the string data to be a valid semantic verions"""
        
        if version == '': # the only initial validation: may be a partial version
            self._data = semantic_version.Version(data, partial=True) #!?            
            return True

#        try:
        self.set_data( semantic_version.validate(data) )
        return True
#        except:
#            return False

###############################################################
class BaseString(BaseScalar):
    def __init__(self, parent):
        BaseScalar.__init__(self, parent)
        
    def validate(self, version, data):
        """check whether data is a valid string"""
        ### TODO: Detect other YAML scalar types?
        try:
            self.set_data( text_type(data) )
            return True
        except:
            print( "ERROR: Cannot conver '{}' into string!" % format(data) )
            self.set_data( data )


###############################################################
class BaseUIString(BaseString): # visible to user => non empty!
    def __init__(self, parent):
        BaseString.__init__(self, parent)
        
    def validate(self, version, data):
        """check whether data is a valid string"""
        _ret = BaseString.validate(self, version, data)
        
        _ret = _ret and (self.get_data()) # Non-empty
        return _ret
            
###############################################################
class BaseEnum(BaseString): # TODO: Generalize to not only strings...
    def __init__(self, parent):
        BaseString.__init__(self, parent)
        self._types = [] # will depend on the version...        
        
    def validate(self, version, data):
        """check whether data is a valid string"""
        _ret = BaseString.validate(self, version, data)
        
        _ret = _ret and (self.get_data() in self._types) # check withing a list of possible string values
        return _ret
       
###############################################################
class ServiceType(BaseEnum):            ## Q: Is 'Service::type' mandatory? default: 'compose'
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)
        
        _v = 'compose'
        self._types = [_v] # NOTE: will depend on format version!
        self._default_data = _v
        
###############################################################
class StationOMDTag(BaseEnum):          ## Q: Is 'Station::omd_tag' mandatory? default: 'standalone'
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)
        
        _v = 'standalone'
        self._types = ['agent', 'windows', _v] # possible values of omd_tag # will depend on format version!
        self._default_data = _v
        
###############################################################
class StationPowerOnMethodType(BaseEnum): # Enum: [WOL], AMTvPRO, DockerMachine
    def __init__(self, parent):
        BaseEnum.__init__(self, parent)
        
        _v = 'WOL'
        self._types = ['AMTvPRO', 'DockerMachine', _v] # possible values of PowerOnMethod::type # will depend on format version!
        self._default_data = _v
        
###############################################################
class URI(BaseString):
    def __init__(self, parent):
        BaseString.__init__(self, parent)
        
    def validate(self, version, data):
        """check whether data is a valid URI"""
        _ret = BaseString.validate(self, version, data)
        
        # TODO: Check if file exists?        
        return _ret

###############################################################
import re, tokenize

if PY3:
    def is_valid_id(id):
        return id.isidentifier()
elif PY2:
    def is_valid_id(id):
        return re.match(tokenize.Name + '$', id)
else:
    raise NotImplementedError("Unsupported Python version: '{}'".format(version_info))
    
###############################################################
class BaseID(BaseString):
    def __init__(self, parent):
        BaseString.__init__(self, parent)
        
    def validate(self, version, data):
        """check whether data is a valid ID string"""
        _ret = BaseString.validate(self, version, data)
        _ret = _ret and is_valid_id(self.get_data())
        return _ret


###############################################################
class ClientVariable(BaseID): #
    def __init__(self, parent):
        BaseID.__init__(self, parent)

    def validate(self, version, data):
        """check whether data is a valid ID string"""
        _ret = BaseID.validate(self, version, data)

        v = self.get_data()
        
        _ret = _ret and ( v == v.lower() or v == v.upper() ) #! Variables are all lower or upper case!
        _ret = _ret and (re.match("^hilbert(_[a-z0-9]+)+$", v.lower())) # starting with hilbert_ or HILBERT_ with letters, digits and '_'        
        return _ret
    
###############################################################
class ServiceID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)
        # TODO: move uniqueness check here???
        
class ApplicationID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)

###############################################################
class GroupID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)
        # TODO: move uniqueness check here???
        
class StationID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)

class ProfileID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)

###############################################################
class PresetID(BaseID):
    def __init__(self, parent):
        BaseID.__init__(self, parent)
    
###############################################################
class AutoDetectionScript(BaseString):
    def __init__(self, parent):
        BaseString.__init__(self, parent)
        
    def validate(self, version, data):
        """check whether data is a valid script"""
        _ret = BaseString.validate(self, version, data)
        
        # TODO: Check the script?
        return _ret

###############################################################
class DockerComposeServiceName(BaseString):
    def __init__(self, parent):
        BaseString.__init__(self, parent)        
        
    def validate(self, version, data):
        """check whether data is a valid service name in file due to DockerComposeRef"""
        
        _ret = BaseString.validate(self, version, data)
        # TODO: Check the corresponding file for such a service -> Service!
        return _ret

###############################################################
class DockerComposeRef(URI):
    def __init__(self, parent):
        URI.__init__(self, parent)
        self._default_data = "docker-compose.yml"
        
    def validate(self, version, data):
        """check whether data is a valid docker-compose file name"""
        _ret = URI.validate(self, version, data)
        
        ### TODO: call docker-compose on the referenced file!
        return _ret

###############################################################
class Icon(URI):
    def __init__(self, parent):
        URI.__init__(self, parent)
        
    def validate(self, version, data):
        """check whether data is a valid icon file name"""
        _ret = URI.validate(self, version, data)
        
        ### TODO: check the file contents (or extention)
        return _ret
        
###############################################################
class HostAddress(BaseString):
    """SSH alias"""
    
    def __init__(self, parent):
        BaseString.__init__(self, parent)        
        
    def validate(self, version, data):
        """check whether data is a valid ssh alias?"""
        
        _ret = BaseString.validate(self, version, data)
        
        #! TODO: Check for ssh alias!
        return _ret

class HostMACAddress(BaseString):
    """MAC Address of the station"""
    
    def __init__(self, parent):
        BaseString.__init__(self, parent)        
        
    def validate(self, version, data):
        """check whether data is a valid ssh alias?"""
        
        _ret = BaseString.validate(self, version, data)
        
        v = self.get_data()
        
        #! TODO: Check for MAC Address?
        if not re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", v.lower()):
            print ( "Wrong MAC Address: [{}]" . format(data) )
            _ret = False
            
        return _ret

###############################################################
class BaseBool(BaseScalar):
    def __init__(self, parent):
        BaseScalar.__init__(self, parent)
        
    def validate(self, version, data):
        """check whether data is a valid string"""
        ### TODO: Detect other YAML scalar types?

        if (data == True) or (data == False):
            self.set_data( data )
            return True
        
        return False

class StationVisibility(BaseBool): ## "hidden": True / [False]
    def __init__(self, parent):
        BaseBool.__init__(self, parent)
        self._default_data = False


class AutoTurnon(BaseBool): # Bool, False 
    def __init__(self, parent):
        BaseBool.__init__(self, parent)
        self._default_data = False # no powering on by default!?
        
###############################################################
class VariadicRecord(BaseRecord): # will need BaseRecord.validate!
    """Variadic record. Type is determined by the given 'type' field."""

    def __init__(self, parent):
        BaseRecord.__init__(self, parent)
        
        self._type_tag      = "type"
        self._default_type  = None
        self._types         = {}

    def detect_type(self, version, data):
        """determine the type of variadic data for the format version"""

        assert not (self._default_type is None)
        assert len(self._types) > 0
        assert self._default_type in self._types
        assert self._type_tag in self._types[self._default_type]

        _rule = self._types[self._default_type][self._type_tag]
        
        if _rule[0] and (self._type_tag not in data):
            _lc = data.lc # start of the current mapping            
            (l, c) = (_lc.line, _lc.col)
            
            key_note(self._type_tag, l, c, "Error: Missing mandatory key `{}`") # Raise Exception?
            return None
        
        t = data.get(self._type_tag, self._default_type)

        tt = _rule[1](self)
        if not tt.validate(version, t):
            _lc = data.lc.key(self._type_tag)
            (l, c) = _lc # (_lc.line, _lc.col)
            
            value_error(self._type_tag, t, l, c, "invalid value '{}'") # Raise Exception?
            return None

        self._type = tt
        return tt.get_data()

###############################################################
class StationPowerOnMethod(VariadicRecord):
    """StationPowerOnMethod"""
    
    def __init__(self, parent):
        VariadicRecord.__init__(self, parent)

        self._default_type = "WOL" # ServiceType("compose")?
        
        WOL_rule = {
            self._type_tag: (True,  StationPowerOnMethodType), # Mandatory!
            "auto_turnon":  (False, AutoTurnon),
            "mac":          (True,  HostMACAddress)
        }

        DM_rule = {
            self._type_tag:    (True,  StationPowerOnMethodType), # Mandatory!
            "auto_turnon":     (False, AutoTurnon),
            "vm_name":         (True,  BaseString),
            "vm_host_address": (True,  HostAddress)
        }
        
        self._types = { self._default_type: WOL_rule, "DockerMachine": DM_rule } #! NOTE: AMT - maybe later...
   
###############################################################
class Service(VariadicRecord):
    """Service data type"""
    
    def __init__(self, parent):
        VariadicRecord.__init__(self, parent)

        self._default_type = "compose" # ServiceType("compose")?

        self._hook_tag      = "auto_detections"
        self._name_tag      = "name"
        self._file_tag      = "file"
        
        compose_rule = {
            self._type_tag: (True,  ServiceType), # Mandatory
            self._hook_tag: (False, AutoDetectionScript),
            self._name_tag: (True,  DockerComposeServiceName),
            self._file_tag: (False, DockerComposeRef) 
        }

        self._types = { self._default_type: compose_rule }
    
    def validate(self, version, data):
        _ret = VariadicRecord.validate(self, version, data)
        
        ### TODO: call docker-compose on the referenced file with the given Service Name
        return _ret

###############################################################
class Application(Service):
    """Application"""
    
    def __init__(self, parent):
        Service.__init__(self, parent)
    
        self._default_type = "compose" # ServiceType("compose")?
        
        compose_rule = {
            self._type_tag: (True,  ServiceType), # Mandatory
            self._hook_tag: (False, AutoDetectionScript),
            self._name_tag: (True,  DockerComposeServiceName),
            self._file_tag: (False, DockerComposeRef),
            "name":         (True,  BaseUIString),
            "description":  (True,  BaseUIString),
            "icon":         (False, Icon),
            "compatibleStations": (True, Group)
        }
        
        self._types = { self._default_type: compose_rule }

###############################################################
class Profile(BaseRecord):
    """Profile"""
    
    def __init__(self, parent):
        BaseRecord.__init__(self, parent)
    
        self._default_type = "default_profile"
        
        default_rule = {
            "name":         (True,  BaseUIString),
            "description":  (True,  BaseUIString),
            "icon":         (False, Icon),
            "services":     (True, ServiceList)
        }
        
        self._types = { self._default_type: default_rule }


###############################################################
class StationSSHOptions(BaseRecord): # optional: "Station::ssh_options" # record: user, port, key, key_ref
    """StationSSHOptions"""
    
    def __init__(self, parent):
        BaseRecord.__init__(self, parent)
    
        self._default_type = "default_station_ssh_options"
        
        default_rule = {
            "user":         (False, BaseString),
            "key":          (False, BaseString),
            "port":         (False, BaseString), # TODO: BaseInt??  http://stackoverflow.com/questions/4187185/how-can-i-check-if-my-python-object-is-a-number
            "key_ref":      (False, URI),
        }
        
        self._types = { self._default_type: default_rule }
        
    def validate(self, version, data):
        """check whether data is a valid ssh connection options"""
        
        _ret = BaseRecord.validate(self, version, data)
        
        # TODO: Check for ssh connection: Use some Python SSH Wrapper (2/3)
        return _ret
       
###############################################################
class Station(BaseRecord):
    """Station"""
    
    def __init__(self, parent):
        BaseRecord.__init__(self, parent)
    
        self._default_type = "default_station"
        
        default_rule = {
            "name":         (True,  BaseUIString),
            "description":  (True,  BaseUIString),
            "icon":         (False, Icon),
            "extends":      (False, StationID),
            "profile":      (True, ProfileID),
            "address":      (True,  HostAddress),
            "poweron_settings": (False, StationPowerOnMethod), # !! variadic, PowerOnType...
            "ssh_options":      (False, StationSSHOptions), # !!! record: user, port, key, key_ref
            "omd_tag":      (True, StationOMDTag), # ! like ServiceType: e.g. agent. Q: Is this mandatory?
            "hidden":      (False, StationVisibility), # Q: Is this mandatory?
            "client_settings": (False, StationClientSettings) # IDMap : (BaseID, BaseString)
        }
        
        self._types = { self._default_type: default_rule }
        
    
###############################################################
class BaseIDMap(Base):
    """Mapping: SomeTypeID -> AnyType"""    

    def __init__(self, parent):
        Base.__init__(self, parent)
        self._default_type = None
        self._types = {} # type -> (TypeID, Type)
       
#    def validate_ID(self, key): # special ID type!!!
#        return is_valid_id(key)
    
    def detect_type(self, version, data):
        """determine the type of variadic data for the format version"""
        
        assert not (self._default_type is None)
        assert len(self._types) > 0
        
        return self._default_type
        
    def validate(self, version, data):
        _type = self.detect_type(version, data)
        
        assert not (_type is None)
        assert _type in self._types
        
        (_id, _rule)  = self._types[_type]

        _ret = True

        _lc = data.lc # starting position?
        (s, c) = (_lc.line, _lc.col) 

        _d = {}
        for offset, k in enumerate(data):
            v = data.get(k)
            l = s + offset

            id = _id(self)
            
            if not id.validate(version, k):
                key_error(k, v, l, c, "Invalid Key ID: '{}' (type: '%s')" % (_type)) # Raise Exception?
                _ret = False
            else:
                _d[id] = _rule(self)
                
                if not _d[id].validate(version, v): # TODO: save to self!
                    value_error(k, v, l, c, "invalid value '{}' value (type: '%s')" % (_type)) # Raise Exception?
                    _ret = False
                    
        self.set_data(_d)

        return _ret
        
###############################################################
class GlobalServices(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_services"
        self._types = { self._default_type: (ServiceID, Service) }

    # def validate(self, version, data):
    #     _ret = BaseID.validate(self, version, data)
    #     ### TODO: Any post processing?
    #     return _ret



###############################################################
class StationClientSettings(BaseIDMap): #            "client_settings": (False, StationClientSettings) # IDMap : (BaseID, BaseString)
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_station_client_settings"
        self._types = { self._default_type: (ClientVariable, BaseScalar) } #! TODO: only strings for now! More scalar types?!
    
###############################################################
class GlobalApplications(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_applications"
        self._types = { self._default_type: (ApplicationID, Application) }

    # def validate(self, version, data):
    #     _ret = BaseID.validate(self, version, data)
    #     ### TODO: Any post processing?
    #     return _ret

###############################################################
class GlobalProfiles(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_profiles"
        self._types = { self._default_type: (ProfileID, Profile) }
        
    # def validate(self, version, data):
    #     _ret = BaseID.validate(self, version, data)
    #     ### TODO: Any post processing?
    #     return _ret

###############################################################
class GlobalStations(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_stations"
        self._types = { self._default_type: (StationID, Station) }

    # def validate(self, version, data):
    #     _ret = BaseID.validate(self, version, data)
    #     ### TODO: Any post processing?
    #     return _ret

###############################################################
import collections

if PY2:
    def issequenceforme(obj):
        if isinstance(obj, basestring):
            return False
        return isinstance(obj, collections.Sequence)
elif PY3:
    def issequenceforme(obj):
#        if isinstance(obj, basestring):
#            return False
        # TODO: ???
        return isinstance(obj, collections.Sequence)
else:
    raise NotImplementedError("Unsupported Python version: '{}'".format(version_info))

###############################################################
class BaseList(Base):
    """List of entities of the same type"""
    
    def __init__(self, parent):
        Base.__init__(self, parent)
        
    def detect_type(self, version, data):
        """determine the class of items based on the version and sample data"""
        
        assert not (self._default_type is None)
        assert len(self._types) > 0
        
        return self._types[self._default_type]

    def validate(self, version, data):
        _type = self.detect_type(version, data)
        assert _type is not None

        _lc = data.lc

        if not issequenceforme(data):
            data = [data]
            
        _d = []
        
        _ret = True
        for idx, i in enumerate(data):
            _v = _type(self)
            if not _v.validate(version, i):
                # TODO: error # show _lc
                print( "Error insequence at {}" . format(idx) ) 
                _ret = False
            else:
                _d.insert(idx, _v) # append?
        
        self.set_data(_d)
        return _ret
    

###############################################################
class ServiceList(BaseList):
    """List of ServiceIDs or a single ServiceID!"""
    
    def __init__(self, parent):
        BaseList.__init__(self, parent)

        self._default_type = "default_ServiceID_list"
        self._types = { self._default_type: ServiceID }    

###############################################################
class GroupIDList(BaseList):
    """List of GroupIDs or a single GroupID!"""
    
    def __init__(self, parent):
        BaseList.__init__(self, parent)

        self._default_type = "default_GroupID_list"
        self._types = { self._default_type: GroupID }
        
###############################################################
class Group(BaseRecord): #? TODO: GroupSet & its .parent?
    """Group"""
    
    def __init__(self, parent):
        BaseRecord.__init__(self, parent)

        self._default_type = "default_group"
        
        self._include_tag       = "include"
        self._exclude_tag       = "exclude"
        self._intersectWith_tag = "intersectWith"
        
        default_rule = {
             self._include_tag:        (False,  GroupIDList),
             self._exclude_tag:        (False,  GroupIDList),
             self._intersectWith_tag:  (False,  GroupIDList),
             "name":         (False,  BaseUIString),
             "description":  (False,  BaseUIString),
             "icon":         (False,  Icon)
        }

        self._types = { self._default_type: default_rule }

    def detect_extra_rule(self, version, key, value): # Any extra unlisted keys in the mapping?
        if value is None: # Set item!
            return GroupID        
        return None
        
    def validate(self, version, data):       
        _ret = BaseRecord.validate(self, version, data)
        # Add extra keys into include?
        return _ret     

###############################################################
class GlobalGroups(BaseIDMap):
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_groups"
        self._types = { self._default_type: (GroupID, Group) }
        

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

        self._types = { self._default_type: default_rule }
        
        raise NotImplementedError("Presets are not supported yet!")
    
###############################################################
class GlobalPresets(BaseIDMap): # Dummy for now!
    def __init__(self, parent):
        BaseIDMap.__init__(self, parent)
        self._default_type = "default_global_presets"
        self._types = { self._default_type: (PresetID, Preset) }
        
    def validate(self, version, data):
        print ("Warning: Presets are not supported yet!")
#        raise NotImplementedError("Presets are not supported yet!")
        return True
    
###############################################################
class Global(BaseRecord):
    """General Hilbert Configuration format"""
    
    def __init__(self, parent):
        BaseRecord.__init__(self, parent) # This is the Main Root!

        self._default_type = "default_global"

        self._version_tag      = "Version"
        self._applications_tag = "Applications"
        self._services_tag     = "Services"
        self._profiles_tag     = "Profiles"        
        self._stations_tag     = "Stations"
        self._groups_tag       = "Groups"
        
        ### explicit (optional) Type?
        default_rule = {
            self._version_tag:      (True,  SemanticVersion), # Mandatory, specifies possibly supported Types of each Configuration Entity
            self._services_tag:     (True,  GlobalServices),
            self._applications_tag: (True,  GlobalApplications),
            self._profiles_tag:     (True,  GlobalProfiles),
            self._stations_tag:     (True,  GlobalStations),
            self._groups_tag:       (False, GlobalGroups), # Optional
            "Presets":              (False, GlobalPresets), # Optional. May be removed! default?
        }

        self._types = { self._default_type: default_rule }

    @classmethod
    def parse(cls, data, parent=None):
        self = cls(parent)
        
        if self._version_tag not in data:
            print( "ERROR: Missing '{}' field!" . format(self._version_tag) )

        # TODO: see VariadicRecord :: detect_type to avoid assumptions!
            
        v = SemanticVersion(None)
        
        if not v.validate('', data.get(self._version_tag)): 
            print( "Wrong Global '{}' specification!" . format(self._version_tag) )
                
        _version = v.get_data() # there may be some default verion...
            
        print( "File Format is of version: '{}'" . format(_version) )
        self.set_version(_version)
            
        _ret = self.validate(_version, data) ## TODO: FIXME: should not need version...!?
            
        print( "\nValidation result: '{}'" . format(_ret) )

        return self
        
    def validate(self, version, data):
        _ret = BaseRecord.validate(self, version, data)
      
        for offset, k in enumerate(data):
            if k == self._version_tag:
                if offset != 0:
                    print("Note: '{}' specified correctly but not ahead of everything else (offset: {})!".format(self._version_tag, offset))
                    _ret = False
                break

        #! checks uniqueness of keys among (Services/Applications):
        
        _services = data.get(self._services_tag) # Rely on the above and use get_data?
        _applications = data.get(self._applications_tag)

        for p, k in enumerate(_services):
            _lc = _services.lc.key(k)
            (sline, scol) = _lc # (_lc.line, _lc.col)
            
            if k in _applications:        
                print( "Error: '{}' is both a ServiceID and an ApplicationID:" . format(k) )
                key_error(k, _services[k], sline, scol, "Service key: {}")
                
                _alc = _applications.lc.key(k)
                (aline, acol) = _alc # (_alc.line, _alc.col)
                
                key_error(k, _applications[k], aline, acol, "Application key: {}")

        #! TODO: check Uniqueness of keys among (Profiles/Stations/Groups) !!!!                
        # TODO: check for GroupID <-> StationID <-> ProfileID
        return _ret
        
###############################################################

print( "Python Version: '{}'".format( version_info ) )
print( "ruamel.yaml Version: '{}'".format(yaml.__version__) )

if __name__ == "__main__":    
    usage = "{} <Hilbert.yaml>" . format( argv[0] )
    
    if len(argv[1:]) > 0:
        for arg in argv[1:]:
            print( "Parsing config file: '{}'".format(arg) )
            
            data = load_yaml(arg) # TODO: check that this is a dictionary!

            print( "Input YAML file: " )
            print( yaml.round_trip_dump(data) )

            print( "\nValidation starts:\n")
            hilbert_configuration = Global.parse(data)

            print( hilbert_configuration.get_data() )

    else:
        print(usage)

#else:
#    raise NotImplementedError("Sorry Library usage is not supported yet!")
#    assert False
