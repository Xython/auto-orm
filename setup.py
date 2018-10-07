from setuptools import setup
import os

readme = ""


def auto_modules(root, prefix=''):
    modules = set()
    for each in os.listdir(root):
        joined_path = os.path.join(root, each)
        if not os.path.isdir(joined_path):
            continue

        # to long so split into two conditions
        if each.startswith('__') or each.startswith('.'):
            continue

        module = each
        if prefix:
            module = prefix + '.' + module
        modules.add(module)

        modules.update(auto_modules(joined_path, module))
    return modules


setup(
    name='auto_orm',
    version='0.1',
    keywords='orm, auto',
    description='manage your orm codes easily.',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    python_requires='>=3.6.0',
    url='https://github.com/Xython/auto_orm',
    author='thautwarm',
    author_email='twshere@outlook.com',
    packages=auto_modules('.'),
    entry_points={'console_scripts': [
        'dbg=auto_orm.cmd.cli:dbg_lang_cli',
    ]},
    install_requires=[
        'Redy', 'rbnf>=0.3.21', 'wisepy', 'bytecode==0.7.0', 'yapf',
        'sqlalchemy'
    ],
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    zip_safe=False)
