Comments: delete them; one that survives states a why the code cannot show.

The history of a codebase should not be encoded in or inferrable from the codebase itself. Systems at rest should look as if they were designed this way from the start. Exceptions exist, including git history and changelogs. Implications include immediate refactors to simplify and remove old patterns, and immediate sweeps and cleanups of code and documentation included with each modification.

Each object has one source: its generator and its inputs. Built `.glb` files are outputs and stay out of the repository.

The repository names only its own components and public dependencies: nothing from the machines that build it (hostnames, paths outside the repository, credentials) and no personal data.
