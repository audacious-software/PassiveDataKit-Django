# PassiveDataKit-Django

[![Build Status](https://travis-ci.org/audaciouscode/PassiveDataKit-Django.svg?branch=master)](https://travis-ci.org/audaciouscode/PassiveDataKit-Django)

## Aptible Deployments

Passive Data Kit now supports standalone deployments to [Aptible](https://www.aptible.com/) for secure installations handling personal health information (PHI). 

To deploy to Aptible:

1. Check out this repository to a local location.
2. Create a new branch of this repository.
3. Rename `Dockerfile.aptible` to `Dockerfile`.
4. Rename `Procfile.aptible` to `Procfile`.
5. Add the renamed files to the new branch.
6. Set up your Aptible environment as described in the [Django Quickstart Guide](https://support.aptible.com/quickstart/python/django).
7. Push your new branch to the remote repository specified by Aptible.
8. Upon successful deployment, log into an interactive terminal using the `aptible ssh` command and run the `migrate`, `collectstatic`, and `createsuperuser` tasks to initialize your Django environment.
9. Exit the terminal and access the Passive Data Kit data administration interface via `https://aptible.url/data/` or the Django admin at `https://aptible.url/data/`.

This is an early feature, so please log any bugs or other issues to the project's issue tracker. 

## License and Other Project Information

Copyright 2015 Audacious Software

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
