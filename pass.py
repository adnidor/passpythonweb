import subprocess
import os
import tempfile

class Pass:
    _PASS_PATH = "/usr/bin/pass"
    _DEFAULT_ENV = { "GNUPGHOME": "/home/yannik/.gnupg" } #XXX
    _GPG_OPTIONS = "--passentry-mode cancel"
    password = None

    def __init__(self, path_to_store):
        if not os.path.isdir(path_to_store):
            raise FileNotFoundError("dir not found")
        if not os.path.isfile(os.path.join(path_to_store, ".gpg-id")):
            raise FileNotFoundError("not a password store")
        self.pass_dir = path_to_store

    def _call_pass_return_output_raise_on_nonzero(self, arguments, cwd=None, env={}, password=None):
        if type(arguments) is not list:
            raise TypeError("arguments must be list")
        cmd = [ self._PASS_PATH ] + arguments
        password_fd,password_path = tempfile.mkstemp()
        password_file = open(password_fd, 'w')
        env_real = {}
        env_real.update(self._DEFAULT_ENV)
        env_real.update(env)
        env_real.update({ "PASSWORD_STORE_GPG_OPTS": self._GPG_OPTIONS+" --password-file '"+password_path+"'",
                          "PASSWORD_STORE_DIR": self.pass_dir })
        if password:
            password_file.write(password+"\n")
        elif self.password is not None:
            password_file.write(self.password+"\n")
        password_file.close()
        try:
            print(repr(env_real))
            output = subprocess.check_output(cmd, universal_newlines=True, cwd=cwd, env=env_real, stderr=subprocess.STDOUT)
        finally:
            os.remove(password_path)
        return output

    @classmethod
    def init_store(cls, path_to_store, gpg_id):
        if not os.path.isdir(path_to_store):
            raise FileNotFoundError("path_to_store must exist")
        if type(gpg_id) is not str:
            raise TypeError("gpg_id must be str")
        if gpg_id == "":
            raise ValueError("gpg_id cannot be empty")
        env = { "PASSWORD_STORE_DIR": path_to_store }
        subprocess.check_call([ cls._PASS_PATH, "init", gpg_id ], env=env)

    def get_password(self, name):
        try:
            contents = self._call_pass_return_output_raise_on_nonzero(["show", name])
        except subprocess.CalledProcessError as e:
            if e.output.strip() == "Error: "+name+" is not in the password store.":
                raise FileNotFoundError(e.output.strip()) from None
            else:
                print(e.output)
                raise e
        return contents.split('\n', 1)[0]
        
