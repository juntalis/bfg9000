import os.path

from . import *
pjoin = os.path.join

is_mingw = platform_name() == 'windows' and env.builder('c++').flavor == 'cc'
is_msvc = env.builder('c++').flavor == 'msvc'


class TestLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, pjoin(examples_dir, '02_library'),
            configure=False, *args, **kwargs
        )

    def test_default(self):
        self.configure()
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
        self.assertExists(shared_library('library'))
        if not is_msvc:
            self.assertNotExists(static_library('library'))

    def test_static(self):
        self.configure(extra_args=['--disable-shared', '--enable-static'])
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
        self.assertExists(static_library('library'))
        self.assertNotExists(shared_library('library'))

    @unittest.skipIf(is_msvc, 'dual-use libraries collide on msvc')
    def test_dual(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
        self.assertExists(shared_library('library'))
        if platform_name() == 'windows':
            self.assertExists(import_library('library'))
        self.assertExists(static_library('library'))


@unittest.skipIf(is_mingw, 'xfail on mingw (not sure why)')
class TestSharedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'shared_library', install=True, *args,
                                 **kwargs)

    def test_build(self):
        self.build()

        env = None
        if platform_name() == 'windows':
            env = {'PATH': os.pathsep.join([
                os.path.abspath(self.target_path(output_file(i)))
                for i in ('outer', 'middle', 'inner')
            ])}
        self.assertOutput([executable('program')], 'hello, library!\n',
                          env=env)

    @skip_if_backend('msbuild')
    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            pjoin(self.bindir, executable('program').path),
            pjoin(self.libdir, shared_library('inner/inner').path),
            pjoin(self.libdir, shared_library('middle/middle').path),
            pjoin(self.libdir, shared_library('outer/outer').path),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)

        env = None
        if platform_name() == 'windows':
            env = {'PATH': os.pathsep.join([
                os.path.abspath(os.path.join(
                    self.libdir, self.target_path(output_file(i))
                )) for i in ('outer', 'middle', 'inner')
            ])}
        self.assertOutput([pjoin(self.bindir, executable('program').path)],
                          'hello, library!\n', env=env)


class TestStaticLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(self, 'static_library', install=True, *args,
                                 **kwargs)

    def test_build(self):
        self.build()
        self.assertOutput(
            [executable('program')],
            'hello from inner\nhello from middle\nhello from outer\n'
        )
        if env.platform.name == 'linux':
            output = self.assertPopen(['readelf', '-s', executable('program')])
            assertNotRegex(self, output, r"Symbol table '.symtab'")

    @skip_if_backend('msbuild')
    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            pjoin(self.libdir, static_library('inner').path),
            pjoin(self.libdir, static_library('middle').path),
            pjoin(self.libdir, static_library('outer').path),
        ])


class TestDualUseLibrary(IntegrationTest):
    lib_names = ['inner', 'middle', 'outer']

    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, 'dual_use_library', configure=False, install=True, *args,
            **kwargs
        )

    def test_default(self):
        self.configure()
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
        for i in self.lib_names:
            self.assertExists(shared_library(i))
            if platform_name() == 'windows':
                self.assertExists(import_library(i))
            if not is_msvc:
                self.assertNotExists(static_library(i))

    def test_static(self):
        self.configure(extra_args=['--disable-shared', '--enable-static'])
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
        for i in self.lib_names:
            self.assertNotExists(shared_library(i))
            self.assertExists(static_library(i))

    @unittest.skipIf(is_msvc, 'dual-use libraries collide on msvc')
    def test_dual(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')
        for i in self.lib_names:
            self.assertExists(shared_library(i))
            if platform_name() == 'windows':
                self.assertExists(import_library(i))
            self.assertNotExists(static_library(i))

    @unittest.skipIf(is_msvc, 'dual-use libraries collide on msvc')
    def test_dual_shared(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])
        self.build(shared_library('outer'))
        for i in self.lib_names:
            self.assertExists(shared_library(i))
            if platform_name() == 'windows':
                self.assertExists(import_library(i))
            self.assertNotExists(static_library(i))

    @unittest.skipIf(is_msvc, 'dual-use libraries collide on msvc')
    def test_dual_static(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'])
        self.build(static_library('outer'))
        for i in self.lib_names:
            self.assertNotExists(shared_library(i))
            if platform_name() == 'windows':
                self.assertNotExists(import_library(i))
            self.assertExists(static_library(i))

    @unittest.skipIf(is_msvc, 'dual-use libraries collide on msvc')
    @skip_if_backend('msbuild')
    def test_dual_install(self):
        self.configure(extra_args=['--enable-shared', '--enable-static'] +
                       self.extra_args)
        self.build('install')

        self.assertDirectory(self.installdir, (
            [pjoin(self.bindir, executable('program').path)] +
            [pjoin(self.libdir, shared_library(i).path)
             for i in self.lib_names]
        ))

    @unittest.skipIf(is_msvc, 'dual-use libraries collide on msvc')
    @skip_if_backend('msbuild')
    def test_dual_install_libs(self):
        self.configure(extra_args=['--enable-shared', '--enable-static',
                                   '--install-libs'] + self.extra_args)
        self.build('install')

        import_libs = []
        if platform_name() == 'windows':
            import_libs = [pjoin(self.libdir, import_library('outer').path)]
        self.assertDirectory(self.installdir, (
            [pjoin(self.libdir, shared_library(i).path)
             for i in self.lib_names] +
            [pjoin(self.libdir, static_library(i).path)
             for i in self.lib_names] +
            import_libs
        ))


@unittest.skipIf(env.platform.name == 'windows',
                 'no versioned libraries on windows')
class TestVersionedLibrary(IntegrationTest):
    def __init__(self, *args, **kwargs):
        IntegrationTest.__init__(
            self, 'versioned_library', install=True, *args, **kwargs
        )

    def test_build(self):
        self.build()
        self.assertOutput([executable('program')], 'hello, library!\n')

    def test_install(self):
        self.build('install')

        self.assertDirectory(self.installdir, [
            pjoin(self.bindir, executable('program').path),
            pjoin(self.libdir, shared_library('library', '1.2.3').path),
            pjoin(self.libdir, shared_library('library', '1').path),
        ])

        os.chdir(self.srcdir)
        cleandir(self.builddir)
        self.assertOutput([pjoin(self.bindir, executable('program').path)],
                          'hello, library!\n')
