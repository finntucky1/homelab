# Docker Compose

This directory will hold sanitized copies of the actual service definitions.
No deployable stack has been imported yet, because host paths, image versions,
user IDs, networks, and existing deployment methods are unverified.

## Import a stack

1. Locate the actual Compose source or Portainer stack definition. Preserve all
   override files and note how the existing stack is started.
2. Work on a private copy. Document image tags or digests, bind mounts, named
   volumes, service dependencies, restart policies, and required environment
   variable names. Do not export resolved environment values into this repo.
3. Create a sanitized copy here, replacing credentials and identifying values.
   Put placeholder variable names in an `.env.example` alongside it.
4. Validate with the same Compose file order used by the live stack. For a
   single file, from its directory:

   ```sh
   docker compose -f compose.yaml config --quiet
   ```

5. Review the diff before committing. Syntax validation does not verify file
   permissions, mount availability, application behavior, or runtime access.

For every stack, include its purpose, persistent-data locations, update steps,
recovery steps, and the date it was tested. Do not run `up` against a second
copy of the existing stack until names, volumes, and ports have been checked.

Reference: [Docker Compose configuration validation](https://docs.docker.com/reference/cli/docker/compose/config/).
