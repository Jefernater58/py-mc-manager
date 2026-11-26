import argparse
import hashlib
import pathlib
import json
import jdk
import os
import requests

VERSIONS_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

INSTANCES_DIR = "./instances/"
JAVA_DIR = "./java/"

if not pathlib.Path("./config.json").is_file():
    with open("./config.json", "w") as config_file:
        config_file.write("{}")
    config_json = {}

else:
    with open("./config.json", "r") as config_file:
        config_json = json.load(config_file)

if not pathlib.Path("./instances.json").is_file():
    with open("./instances.json", "w") as instances_file:
        instances_file.write("{}")

parser = argparse.ArgumentParser(
                    prog='py-mc-manager',
                    description='Manages Minecraft stuff')

main_subparsers = parser.add_subparsers(dest="action")

### instance ###
instance_parser = main_subparsers.add_parser("instance")
instance_subparsers = instance_parser.add_subparsers(dest="instance_command")

# instance new
instance_new_parser = instance_subparsers.add_parser("new")
instance_new_parser.add_argument("version", help="Minecraft version to use")
instance_new_parser.add_argument("name", help="name of the new instance")
instance_new_parser.add_argument("-m", "--mod-loader", help="vanilla | fabric | forge")

# instance run
instance_run_parser = instance_subparsers.add_parser("run")
instance_run_parser.add_argument("name", help="name of the instance")
instance_run_parser.add_argument("-a", "--args", help="Java arguments")

# instance delete
instance_delete_parser = instance_subparsers.add_parser("delete")
instance_delete_parser.add_argument("name", help="name of the instance to delete")

# instance mods
instance_mods_parser = instance_subparsers.add_parser("mods")
## TODO add another subparser here for mods commands

java_parser = main_subparsers.add_parser("java")
## TODO java arguments

args = parser.parse_args()

def get_downloaded_java_versions():
    ## check if INSTANCES_DIR exists
    if not pathlib.Path(JAVA_DIR).is_dir():
        os.mkdir(JAVA_DIR)
        return []
    else:
        return [item.name for item in pathlib.Path(JAVA_DIR).iterdir() if item.is_dir()]

def new_instance():
    ## TODO implement downloading of modded clients
            
    ## check if instance of the same name already exists
    instance_dir = INSTANCES_DIR + args.name + "/"
    
    if pathlib.Path(instance_dir).is_dir():
        print(f"error: instance with name \"{args.name}\" already exists.")
        exit(1)

    ## check online database for the version
    print(f"Checking for version \"{args.version}\"...")

    versions_json = requests.get(VERSIONS_URL).json()

    version = args.version
    version_url = None

    if version == "latest":
        version = versions_json["latest"]["release"]
    elif version == "snapshot":
        version = versions_json["latest"]["snapshot"]

    for version_obj in versions_json["versions"]:
        if version_obj["id"] == version:
            version_url = version_obj["url"]
            break

    if version_url == None:
        print(f"error: unable to find Minecraft version \"{version}\"")
        exit(1)

    ## download client .jar and check against sha1
    print(f"downloading version \"{version}\"...")

    client_json = requests.get(version_url).json()

    jar_url = client_json["downloads"]["client"]["url"]
    jar_sha1 = client_json["downloads"]["client"]["sha1"]

    jar_bytes = requests.get(jar_url).content

    print(f"checking sha1 checksum...")
    sha1 = hashlib.sha1(jar_bytes)
    if sha1.hexdigest() != jar_sha1:
        print("error: jar sha1 does not match, aborting.")
        exit(1)

    ## TODO check if java version is downloaded. if not, download it.
    java_version = str(client_json["javaVersion"]["majorVersion"])

    # there is no LTS for version 16, JRE 17 is backwards-compatible
    if java_version == "16":
        java_version = "17"

    print(f"checking for installed java version \"{java_version}\"...")

    if java_version not in get_downloaded_java_versions():
        ## download it
        print(f"downloading java version \"{java_version}\"...")
        try: 
            jdk.install(java_version, jre=True, path=JAVA_DIR + java_version)
        except jdk.JdkError:
            print(f"error: HTTP Error 404: unable to download JRE version {java_version}")
            exit(1)


    ## create instance directory and save client .jar
    os.mkdir(instance_dir)
    with open(instance_dir + "client.jar", "wb") as client_jar:
        client_jar.write(jar_bytes)

    ## update instances.json


    print(f"done! New instance created at {pathlib.Path(instance_dir).resolve()}")

def run_instance():
    pass

if args.action == "instance":
    ## check if INSTANCES_DIR exists
    if not pathlib.Path(INSTANCES_DIR).is_dir():
        os.mkdir(INSTANCES_DIR)

    if args.instance_command is None:
        print("error: argument instance_command: must not be empty")
        exit(1)

    elif args.instance_command == "new":
        new_instance()

    elif args.instance_command == "run":
        run_instance()

    elif args.instance_command == "delete":
        pass

    elif args.instance_command == "mods":
        pass

elif args.action == "java":
    pass
