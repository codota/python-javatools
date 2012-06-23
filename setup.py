#! /usr/bin/env python2

# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see
# <http://www.gnu.org/licenses/>.



"""

author: Christopher O'Brien  <obriencj@gmail.com>
license: LGPL
"""



from distutils.core import setup, Command
from distutils.command.build_py import build_py as _build_py



class build_py(_build_py):

    """ Distutils build_py command with some special handling for
    Cheetah tmpl files. Takes tmpl from package source directories and
    compiles them for distribution. This allows me to write tmpl files
    in the src dir of my project, and have them get compiled to
    py/pyc/pyo files during the build process. """


    def initialize_options(self):
        _build_py.initialize_options(self)

        # storage for py files that were created from tmpl files
        self.built_templates = list()


    def find_package_templates(self, package, package_dir):
        # template files will be located under src, and will end in .tmpl

        from os.path import basename, join, splitext
        from glob import glob

        self.check_package(package, package_dir)
        template_files = glob(join(package_dir, "*.tmpl"))
        templates = []

        for f in template_files:
            template = splitext(basename(f))[0]
            templates.append((package, template, f))
        return templates


    def build_package_templates(self):
        for package in self.packages:
            package_dir = self.get_package_dir(package)
            templates = self.find_package_templates(package, package_dir)

            for package_, template, template_file in templates:
                assert package == package_
                self.build_template(template, template_file, package)


    def build_template(self, template, template_file, package):
        # Compile the cheetah template in src into a python file in build

        from Cheetah.Compiler import Compiler
        from os import makedirs
        from os.path import exists, join
        from distutils.util import newer

        comp = Compiler(file=template_file, moduleName=template)
        outfd = join(self.build_lib, *package.split("."))
        outfn = join(outfd, template+".py")

        if not exists(outfd):
            makedirs(outfd)

        if newer(template_file, outfn):
            self.announce("compiling %s -> %s" % (template_file, outfd), 2)
            with open(outfn, "w") as output:
                output.write(str(comp))

        self.built_templates.append(outfn)


    def get_outputs(self, include_bytecode=1):
        # Overridden to append our compiled templates

        outputs = _build_py.get_outputs(self, include_bytecode)
        outputs.extend(self.built_templates)

        if include_bytecode:
            for filename in self.built_templates:
                if self.compile:
                    outputs.append(filename + "c")
                if self.optimize > 0:
                    outputs.append(filename + "o")

        return outputs

    
    def run(self):
        if self.packages:
            self.build_package_templates()
        _build_py.run(self)



class pylint_cmd(Command):

    """ Distutils command to run pylint on the built output and emit
    its results into build/pylint """


    user_options = list()


    def initialize_options(self):
        self.build_base = None
        self.build_lib = None
        self.build_scripts = None


    def finalize_options(self):
        from os.path import join

        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('build_lib', 'build_lib'),
                                   ('build_scripts', 'build_scripts'))

        self.packages = self.distribution.packages
        self.report = join(self.build_base, "pylint")


    def has_pylint(self):
        try:
            from pylint import lint
        except ImportError, ie:
            return False
        else:
            return True


    def run_linter(self):
        from pylint.lint import PyLinter
        import sys

        linter = PyLinter()
        linter.load_default_plugins()

        # using error_mode for now. Need to delve further into
        # PyLinter's reporting so that we can get it to output into
        # the right place and so we can collect the overall
        # results. But this is a good, simple start.
        linter.error_mode()

        # TODO:
        # output pylint report into report dir
        # announce overview (quality %, number of errors and warnings)

        if self.packages:
            self.announce("checking packages", 2)
            linter.check(self.packages)

        if self.build_scripts:
            self.announce("checking scripts", 2)
            linter.check(self.build_scripts)


    def run(self):
        import sys

        if not self.has_pylint():
            self.announce("pylint not present", 2)
            return

        # since we process the build output, we need to ensure build
        # is run first
        self.run_command("build")

        # we'll be running our linter on the contents of the build_lib
        sys.path.insert(0, self.build_lib)
        try:
            self.run_linter()
        finally:
            sys.path.pop(0)

        

setup(name = "javaclass",
      version = "1.3",
      
      packages = ["javaclass",
                  "javaclass.cheetah"],

      package_dir = {"javaclass": "src",
                     "javaclass.cheetah": "src/cheetah"},
      
      package_data = {"javaclass.cheetah": ["data/*.css",
                                            "data/*.js",
                                            "data/*.png"]},
      
      scripts = ["scripts/classdiff",
                 "scripts/classinfo",
                 "scripts/distdiff",
                 "scripts/distinfo",
                 "scripts/jardiff",
                 "scripts/jarinfo",
                 "scripts/manifest",
                 "scripts/distpatchgen"],

      cmdclass = {'build_py': build_py,
                  'pylint': pylint_cmd})



#
# The end.
