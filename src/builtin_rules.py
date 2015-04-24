import os

from builtins import builtin
from languages import ext2lang
import build_inputs
import utils

class SourceFile(build_inputs.Node):
    def __init__(self, name, lang=None):
        build_inputs.Node.__init__(self, name)
        self.lang = lang

class HeaderFile(build_inputs.Node):
    install_kind = 'data'
    install_dir = 'include'

class ObjectFile(build_inputs.Node):
    def __init__(self, name, lang=None):
        build_inputs.Node.__init__(self, name)
        self.lang = lang
        self.in_shared_library = False

class Executable(build_inputs.Node):
    install_kind = 'program'
    install_dir = 'bin'

class Library(build_inputs.Node):
    install_kind = 'program'
    install_dir = 'lib'

class SharedLibrary(Library):
    pass

class StaticLibrary(Library):
    pass

class HeaderDirectory(build_inputs.Directory):
    install_dir = 'include'

#####

class Compile(build_inputs.Edge):
    def __init__(self, target, file, include, options, deps):
        self.file = file
        self.include = include
        self.options = options
        build_inputs.Edge.__init__(self, target, deps)

class Link(build_inputs.Edge):
    def __init__(self, target, files, libs, compile_options, link_options,
                 deps):
        self.files = files
        self.libs = libs
        self.compile_options = compile_options
        self.link_options = link_options
        build_inputs.Edge.__init__(self, target, deps)

class Alias(build_inputs.Edge):
    pass

class Command(build_inputs.Edge):
    def __init__(self, target, cmd, deps):
        self.cmd = cmd
        build_inputs.Edge.__init__(self, target, deps)

#####

@builtin
def header(build, name):
    return HeaderFile(name)

@builtin
def object_file(build, name=None, file=None, include=None, options=None,
                lang=None, deps=None):
    if file is None:
        raise TypeError('"file" argument must not be None')
    if lang is None:
        lang = ext2lang.get( os.path.splitext(file)[1] )
    source_file = utils.objectify(file, SourceFile, lang=lang)
    includes = utils.objectify_list(include, HeaderDirectory)

    if name is None:
            name = os.path.splitext(file)[0]
    target = ObjectFile(name, lang)
    build.add_edge(Compile(
        target, source_file, includes, utils.shell_listify(options), deps
    ))
    return target

@builtin
def object_files(build, files, include=None, options=None, lang=None):
    return [object_file(build, file=f, include=include, options=options,
                        lang=lang) for f in files]

def _binary(build, target, files, libs=None, lang=None,
            include=None, compile_options=None, link_options=None, deps=None):
    def make_obj(x):
        return object_file(build, file=x, include=include,
                           options=compile_options, lang=lang)

    build.fallback_default = target
    objects = utils.objectify_list(files, ObjectFile, make_obj)
    libs = utils.objectify_list(libs, Library, external=True)
    link = Link(target, objects, libs, utils.shell_listify(compile_options),
                utils.shell_listify(link_options), deps)
    build.add_edge(link)
    return link

@builtin
def executable(build, name, *args, **kwargs):
    target = Executable(name)
    _binary(build, target, *args, **kwargs)
    return target

@builtin
def shared_library(build, name, *args, **kwargs):
    target = SharedLibrary(name)
    rule = _binary(build, target, *args, **kwargs)
    for f in rule.files:
        f.in_shared_library = True
    return target

@builtin
def static_library(build, name, *args, **kwargs):
    target = StaticLibrary(name)
    _binary(build, target, *args, **kwargs)
    return target

@builtin
def alias(build, name, deps):
    target = build_inputs.Node(name)
    build.add_edge(Alias(target, deps))
    return target

@builtin
def command(build, name, cmd, deps=None):
    target = build_inputs.Node(name)
    build.add_edge(Command(target, cmd, deps))
    return target

#####

@builtin
def default(build_inputs, *args):
    build_inputs.default_targets.extend(args)

@builtin
def install(build, *args):
    for i in args:
        if isinstance(i, build_inputs.Directory):
            build.install_targets.directories.append(i)
        else:
            default(build, i)
            build.install_targets.files.append(i)

@builtin
def header_directory(build, directory):
    return HeaderDirectory(directory)