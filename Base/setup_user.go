package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/user"
	"strconv"
	"strings"

	"github.com/urfave/cli/v3"
)

func main() {
	var (
		userName    string
		groupName   string
		uid         int
		gid         int
		home        string
		extraGIDs   []int
		extraGroups []string
	)

	cmd := &cli.Command{
		Name:  "setup-user",
		Usage: "Configure user/group used in container",
		Flags: []cli.Flag{
			&cli.StringFlag{
				Name:        "user",
				Usage:       "User name",
				Destination: &userName,
				Sources:     cli.EnvVars("PUSER"),
			},
			&cli.StringFlag{
				Name:        "group",
				Usage:       "Group name",
				Destination: &groupName,
				Sources:     cli.EnvVars("PGROUP"),
			},
			&cli.IntFlag{
				Name:        "uid",
				Usage:       "User ID",
				Destination: &uid,
				Sources:     cli.EnvVars("PUID"),
			},
			&cli.IntFlag{
				Name:        "gid",
				Usage:       "Group ID",
				Destination: &gid,
				Sources:     cli.EnvVars("PGID"),
			},
			&cli.StringFlag{
				Name:        "home",
				Usage:       "Home directory",
				Destination: &home,
				Sources:     cli.EnvVars("HOME"),
			},
			&cli.IntSliceFlag{
				Name:        "extra-gid",
				Usage:       "Extra GID(s)",
				Destination: &extraGIDs,
				Sources:     cli.EnvVars("EXTRA_GIDS"),
			},
			&cli.StringSliceFlag{
				Name:        "extra-group",
				Usage:       "Extra group(s)",
				Destination: &extraGroups,
				Sources:     cli.EnvVars("EXTRA_GROUPS"),
			},
		},
		Action: func(ctx context.Context, cmd *cli.Command) error {
			var (
				unknownUserIdError  user.UnknownUserIdError
				unknownUserError    user.UnknownUserError
				unknownGroupIdError user.UnknownGroupIdError
				unknownGroupError   user.UnknownGroupError
			)

			createUser := false
			createGroup := false

			if cmd.IsSet("uid") {
				fmt.Printf("echo UID set to %d\n", uid)
				userExisting, err := user.LookupId(strconv.Itoa(uid))
				if !errors.As(err, &unknownUserIdError) {
					checkError(err)
				}
				if userExisting == nil {
					createUser = true
				} else {
					if cmd.IsSet("user") && userExisting.Username != userName {
						return fmt.Errorf("UID %d has been occupied by user '%s'", uid, userExisting.Username)
					}
					userName = userExisting.Username
					home = userExisting.HomeDir
				}
			}

			if cmd.IsSet("user") {
				fmt.Printf("echo User set to '%s'\n", userName)
				userExisting, err := user.Lookup(userName)
				if !errors.As(err, &unknownUserError) {
					checkError(err)
				}
				if userExisting == nil {
					createUser = true
				} else {
					if cmd.IsSet("uid") && userExisting.Uid != strconv.Itoa(uid) {
						return fmt.Errorf("user '%s' already exists with UID %s", userName, userExisting.Uid)
					}
					uid, _ = strconv.Atoi(userExisting.Uid)
					home = userExisting.HomeDir
				}
			}

			if userName == "" {
				userName = fmt.Sprintf("user%d", uid)
			}
			export("PUSER", userName)

			if cmd.IsSet("gid") {
				fmt.Printf("echo GID set to %d\n", gid)
				groupExisting, err := user.LookupGroupId(strconv.Itoa(gid))
				if !errors.As(err, &unknownGroupIdError) {
					checkError(err)
				}
				if groupExisting == nil {
					createGroup = true
				} else {
					if cmd.IsSet("group") && groupExisting.Name != groupName {
						return fmt.Errorf("GID %d has been occupied by group '%s'", gid, groupExisting.Name)
					}
					groupName = groupExisting.Name
				}
			}

			if cmd.IsSet("group") {
				fmt.Printf("echo Group set to '%s'\n", groupName)
				groupExisting, err := user.LookupGroup(groupName)
				if !errors.As(err, &unknownGroupError) {
					checkError(err)
				}
				if groupExisting == nil {
					createGroup = true
				} else {
					if cmd.IsSet("gid") && groupExisting.Gid != strconv.Itoa(gid) {
						return fmt.Errorf("group '%s' already exists with GID %s", groupName, groupExisting.Gid)
					}
					gid, _ = strconv.Atoi(groupExisting.Gid)
				}
			}

			if groupName == "" {
				groupName = userName
			}
			export("PGROUP", groupName)

			if home != "" {
				if _, err := os.Stat(home); os.IsNotExist(err) {
					log("Home directory '%s' not found. Creating it now...", home)
					run("mkdir", "-p", home)
					export("HOME", home)
				} else if err != nil {
					return fmt.Errorf("failed to check home directory status: %w", err)
				}
			}

			if createGroup {
				addgroupArgs := []string{}
				if cmd.IsSet("gid") {
					addgroupArgs = append(addgroupArgs, "--gid", strconv.Itoa(gid))
				}
				addgroupArgs = append(addgroupArgs, groupName)
				log("Create group %s", groupName)
				run("addgroup", addgroupArgs...)
			}

			if createUser {
				adduserArgs := []string{"--gecos", "", "--disabled-password", "--no-create-home"}
				if cmd.IsSet("uid") {
					adduserArgs = append(adduserArgs, "--uid", strconv.Itoa(uid))
				}
				adduserArgs = append(adduserArgs, "--group", groupName)
				adduserArgs = append(adduserArgs, userName)
				log("Create user %s", userName)
				run("adduser", adduserArgs...)

				if home != "" {
					log("Set ownership of home directory")
					run("chown", "-R", fmt.Sprintf("%s:%s", userName, groupName), home)
					log("Set user's home directory")
					run("usermod", "-d", home, userName)
				}

				for _, extraGid := range extraGIDs {
					extraGroupName := fmt.Sprintf("group%d", extraGid)
					log("Create group for extra GID %d", extraGid)
					run("addgroup", "--gid", strconv.Itoa(extraGid), extraGroupName)
					extraGroups = append(extraGroups, extraGroupName)
				}

				for _, extraGroup := range extraGroups {
					log("Add user %s to extra group %s", userName, extraGroup)
					run("usermod", "-aG", extraGroup, userName)
				}
			}

			return nil
		},
	}

	err := cmd.Run(context.Background(), os.Args)
	checkError(err)
}

func export(name string, value string) {
	fmt.Printf("export %s=%s\n", name, strconv.Quote(value))
}

func log(format string, a ...any) {
	fmt.Printf("echo %s\n", fmt.Sprintf(format, a...))
}

func run(name string, arg ...string) {
	fmt.Printf("%s %s\n", name, strings.Join(arg, " "))
}

func checkError(err error) {
	if err != nil {
		fmt.Printf("[ERROR] %s\n", err)
		os.Exit(1)
	}
}
