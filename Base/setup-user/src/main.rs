use anyhow::{bail, Result};
use clap::Parser;
use nix::unistd::{Gid, Group, Uid, User};
use std::path::Path;

macro_rules! strings {
    ( $( $x:expr ),* $(,)? ) => {
        vec![
            $(
                $x.to_string(),
            )*
        ]
    };
}

macro_rules! export {
    ($name:expr, $value:expr) => {
        println!("export {}={:?}", $name, $value)
    };
}

macro_rules! log {
    ($($arg:tt)*) => {
        println!("echo {}", format!($($arg)*))
    };
}

macro_rules! run {
    ($cmd:expr) => {
        println!("{}", $cmd)
    };

    ($cmd:expr, args $args:expr) => {
        println!("{} {}", $cmd, $args.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "))
    };

    ($cmd:expr, $($arg:expr),+ $(,)?) => {
        println!("{} {}", $cmd, vec![$($arg.to_string()),*].join(" "))
    };
}

#[derive(Parser)]
#[command(name = "setup-user", about = "Configure user/group used in container")]
struct Args {
    #[arg(long, env = "PUSER", help = "User name")]
    user: Option<String>,

    #[arg(long, env = "PGROUP", help = "Group name")]
    group: Option<String>,

    #[arg(long, env = "PUID", help = "User ID")]
    uid: Option<u32>,

    #[arg(long, env = "PGID", help = "Group ID")]
    gid: Option<u32>,

    #[arg(long, env, help = "Home directory")]
    home: Option<String>,

    #[arg(long = "extra-gid", env, value_delimiter = ',', help = "Extra GID(s)")]
    extra_gids: Vec<u32>,

    #[arg(
        long = "extra-group",
        env,
        value_delimiter = ',',
        help = "Extra group(s)"
    )]
    extra_groups: Vec<String>,
}

fn main() -> Result<()> {
    let mut args = Args::parse();

    let should_create_user = resolve_user(&mut args)?;
    let should_create_group = resolve_group(&mut args)?;

    let user_name = args.user.as_ref().unwrap();
    let group_name = args.group.as_ref().unwrap();

    if should_create_group {
        let mut groupadd_args: Vec<String> = strings![];

        if let Some(gid) = args.gid {
            groupadd_args.extend(strings!["--gid", gid]);
        }

        log!("Create group {group_name}");
        groupadd_args.push(group_name.clone());
        run!("groupadd", args & groupadd_args);
    }

    if should_create_user {
        let mut useradd_args: Vec<String> = strings!["--no-create-home", "--no-user-group"];

        if let Some(uid) = args.uid {
            useradd_args.extend(strings!["--uid", uid]);
        }

        useradd_args.extend(strings!["--gid", group_name]);

        log!("Create user {user_name}");
        useradd_args.push(user_name.clone());
        run!("useradd", args & useradd_args);
    }

    let mut extra_groups = args.extra_groups.clone();
    for &gid in &args.extra_gids {
        let extra_group = format!("group{gid}");
        log!("Create group for extra GID {gid}");
        run!("groupadd", "--gid", &gid.to_string(), &extra_group);
        extra_groups.push(extra_group);
    }

    for group in &extra_groups {
        log!("Add user {} to extra group {}", user_name, group);
        run!("usermod", "-aG", group, user_name);
    }

    if let Some(ref home) = args.home {
        if !Path::new(home).exists() {
            log!("Home directory '{home}' not found. Creating it now...");
            run!("mkdir", "-p", home);
        }
        log!("Set ownership of home directory");
        run!("chown", "-R", &format!("{user_name}:{group_name}"), home);
        log!("Set user's home directory");
        run!("usermod", "-d", home, user_name);
        export!("HOME", home);
    }

    Ok(())
}

fn resolve_user(args: &mut Args) -> Result<bool> {
    let mut create = false;

    if let Some(uid) = args.uid {
        log!("UID set to {uid}");
        if let Some(user) = User::from_uid(Uid::from_raw(uid))? {
            if let Some(ref name) = args.user {
                if user.name != *name {
                    bail!("UID {uid} has been occupied by user '{}'", user.name);
                }
            }
            args.user = Some(user.name);
            args.home = Some(user.dir.to_string_lossy().to_string());
        } else {
            create = true;
        }
    }

    if let Some(ref name) = args.user {
        log!("User set to '{name}'");
        if let Some(user) = User::from_name(name)? {
            if let Some(uid) = args.uid {
                if user.uid.as_raw() != uid {
                    bail!(
                        "user '{name}' already exists with UID {}",
                        user.uid.as_raw()
                    );
                }
            }
            args.uid = Some(user.uid.as_raw());
            args.home = Some(user.dir.to_string_lossy().to_string());
        } else {
            create = true;
        }
    }

    if args.user.is_none() {
        if args.uid.is_none() {
            bail!("Either --user (PUSER) or --uid (PUID) must be set");
        }
        args.user = Some(format!("user{}", args.uid.unwrap()));
    }
    export!("PUSER", args.user.as_ref().unwrap());

    Ok(create)
}

fn resolve_group(args: &mut Args) -> Result<bool> {
    let mut create = false;

    if let Some(gid) = args.gid {
        log!("GID set to {gid}");
        if let Some(group) = Group::from_gid(Gid::from_raw(gid))? {
            if let Some(ref name) = args.group {
                if group.name != *name {
                    bail!("GID {gid} has been occupied by group '{}'", group.name);
                }
            }
            args.group = Some(group.name);
        } else {
            create = true;
        }
    }

    if let Some(ref name) = args.group {
        log!("Group set to '{name}'");
        if let Some(group) = Group::from_name(name)? {
            if let Some(gid) = args.gid {
                if group.gid.as_raw() != gid {
                    bail!(
                        "group '{name}' already exists with GID {}",
                        group.gid.as_raw()
                    );
                }
            }
            args.gid = Some(group.gid.as_raw());
        } else {
            create = true;
        }
    }

    if args.group.is_none() {
        args.group = args.user.clone();
    }
    export!("PGROUP", args.group.as_ref().unwrap());

    Ok(create)
}
