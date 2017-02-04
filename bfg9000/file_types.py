from .iterutils import listify as _listify
from .languages import src2lang as _src2lang, hdr2lang as _hdr2lang
from .path import InstallRoot as _InstallRoot
from .safe_str import safe_str as _safe_str


class Node(object):
    private = False

    def __init__(self, path):
        self.creator = None
        self.path = path

    def _safe_str(self):
        return _safe_str(self.path)

    @property
    def all(self):
        return [self]

    def __repr__(self):
        return '<{type} {name}>'.format(
            type=type(self).__name__, name=repr(self.path)
        )

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.path == rhs.path


class Phony(Node):
    pass


class File(Node):
    install_kind = None
    install_root = None

    def __init__(self, path, external=False):
        Node.__init__(self, path)
        self.external = external
        self.post_install = None

    @property
    def install_deps(self):
        return []


class Directory(File):
    def __init__(self, path, files=None, external=False):
        File.__init__(self, path, external)
        self.files = files


class SourceFile(File):
    def __init__(self, path, lang=None, external=False):
        File.__init__(self, path, external)
        self.lang = lang or _src2lang.get(path.ext())


class HeaderFile(File):
    install_kind = 'data'
    install_root = _InstallRoot.includedir

    def __init__(self, path, lang=None, external=False):
        File.__init__(self, path, external)
        self.lang = lang or _hdr2lang.get(path.ext())


class PrecompiledHeader(HeaderFile):
    install_kind = None


class MsvcPrecompiledHeader(PrecompiledHeader):
    def __init__(self, path, object_path, header_name, format, lang,
                 external=False):
        PrecompiledHeader.__init__(self, path, lang, external)
        self.object_file = ObjectFile(object_path, format, self.lang, external)
        self.object_file.private = True
        self.header_name = header_name


class HeaderDirectory(Directory):
    install_kind = 'data'
    install_root = _InstallRoot.includedir

    def __init__(self, path, files=None, system=False, external=False):
        Directory.__init__(self, path, files, external)
        self.system = system


class Binary(File):
    install_kind = 'program'
    install_root = _InstallRoot.libdir

    def __init__(self, path, format, external=False):
        File.__init__(self, path, external)
        self.format = format


class ObjectFile(Binary):
    def __init__(self, path, format, lang, external=False):
        Binary.__init__(self, path, format, external)
        self.lang = lang


# XXX: Perhaps this should be a generic file list that we can use for any kind
# of file?
class JvmClassList(ObjectFile):
    pass


# This is sort of a misnomer. It's really just "a binary that is not an object
# file", even though it's not necessarily been linked.
class LinkedBinary(Binary):
    def __init__(self, *args, **kwargs):
        Binary.__init__(self, *args, **kwargs)
        self.runtime_deps = []
        self.linktime_deps = []

    @property
    def install_deps(self):
        return self.runtime_deps + self.linktime_deps


class Executable(LinkedBinary):
    install_root = _InstallRoot.bindir


class Library(LinkedBinary):
    @property
    def runtime_file(self):
        return None


# This is used for JVM binaries, which can be both executables and libraries.
# Multiple inheritance is a sign that we should perhaps switch to a trait-based
# system though...
class ExecutableLibrary(Executable, Library):
    install_root = _InstallRoot.bindir


class SharedLibrary(Library):
    @property
    def runtime_file(self):
        return self


class LinkLibrary(SharedLibrary):
    def __init__(self, path, library, external=False):
        SharedLibrary.__init__(self, path, library.format, external)
        self.library = library
        self.linktime_deps = [library]

    @property
    def runtime_file(self):
        return self.library


class VersionedSharedLibrary(SharedLibrary):
    def __init__(self, path, format, soname, linkname, external=False):
        SharedLibrary.__init__(self, path, format, external)
        self.soname = LinkLibrary(soname, self, external)
        self.link = LinkLibrary(linkname, self.soname, external)


class ExportFile(File):
    private = True


# This refers specifically to DLL files that have an import library, not just
# anything with a .dll extension (for instance, .NET DLLs are just regular
# shared libraries.
class DllLibrary(SharedLibrary):
    install_root = _InstallRoot.bindir
    private = True

    def __init__(self, path, format, import_name, export_name=None,
                 external=False):
        SharedLibrary.__init__(self, path, format, external)
        self.import_lib = LinkLibrary(import_name, self, external)
        self.export_file = ExportFile(export_name, external)


class StaticLibrary(Library):
    def __init__(self, path, format, langs, external=False):
        Library.__init__(self, path, format, external)
        self.langs = _listify(langs)
        self.forward_args = {}


class WholeArchive(StaticLibrary):
    def __init__(self, library):
        self.library = library

    def __getattribute__(self, name):
        if name in ['library', '_safe_str', '__repr__', '__hash__', '__eq__']:
            return object.__getattribute__(self, name)
        return getattr(object.__getattribute__(self, 'library'), name)


class DualUseLibrary(object):
    def __init__(self, shared, static):
        self.shared = shared
        self.static = static

    @property
    def all(self):
        return [self.shared, self.static]


class Package(object):
    def __init__(self, name):
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, rhs):
        return type(self) == type(rhs) and self.name == rhs.name


# A reference to a macOS framework. XXX: Maybe put this somewhere else?
class Framework(object):
    def __init__(self, name):
        self.name = name

    @property
    def runtime_file(self):
        None
