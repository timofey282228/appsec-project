import logging
import enum
import argparse

from .statutils import *
from .storage import *
from .common_read import *
from .win_read_cli import *
from .model import *


class DisplayableEnum:
    @classmethod
    def help(cls) -> str:
        return ", ".join(f"{i.value} - {i.name}" for i in cls)


class Mode(DisplayableEnum, enum.StrEnum):
    Authenticate = "A"
    Learn = "L"


def learn(ms: Storage):
    username = input("Learn for user: ")
    if ms.get_model(username):
        ans = input(
            "Model for this user already exists. Do you want to replace it? [Y/n]: "
        )
        if ans.lower() == "y":
            pass
        else:
            return

    authphrase = input("Learn authphrase: ")

    while len(authphrase) < 4:
        print(
            "This phrase is too short. Try something with more than 3 (three) characters."
        )
        authphrase = input("")

    times = None
    while not times:
        try:
            times = int(
                input(
                    f"How many references to create (only {LIMIT} will be used, but you will have the ability to train your typing): "
                )
            )

            if times < 1:
                raise ValueError

        except ValueError:
            print("Provide a positive integer")

    print("Now type in the authentication phrase")

    references = []
    for e, r in enumerate(
        get_readings_for(win_read_cli, times=times, auth_phrase=authphrase)
    ):
        significants = significant(r)
        sample_e = expectile(significants)
        sample_d = dispersion(significants)

        if sample_e == 0 or sample_d == 0:
            logging.warning(
                "Got bad measurements, skipping: (%s, %s)", sample_e, sample_d
            )
            continue

        references.append(Reference(expectile=sample_e, variation=sample_d))
        logging.info("Read phrase OK")
        if times - 1 - e > 0:
            print(f"[+] Read phrase OK. {times - 1 - e} to go.")
        else:
            print(f"[+] Read phrase OK.")

    if len(references) == 0:
        logging.error("Could not build a model: all measurements were bad.")
        print(
            "[-] Could not build a model. Try again using a different phrase, or maybe more attempts."
        )
        return

    model = KeypressModel(auth_phrase=authphrase, references=references)
    ms.set_model(username=username, model=model)
    print("[+] Learning finished.")


def match(ref, sample, n) -> bool:
    dh = are_dispersions_homogeneous(ref[1], sample[1], n)
    if not dh:
        return False

    ce = are_centers_equal(ref, sample, n)
    if not ce:
        return False

    return True


def authenticate(ms: Storage, *, a2, a3, threshold, update_threshold, update=True):
    username = input("Authenticate as user: ")
    model = ms.get_model(username)

    if not model:
        print("No model for this username has been recorded")
        return None

    claims_legit_str = input("Are you who you claim to be? (Please be honest) [Y/n]: ")
    if claims_legit_str.lower() == "y":
        print(
            f"[+] Nice to see you, {username}! But you'll still need to authenticate..."
        )
        claims_legit = True
    else:
        print("[+] Ok, that was honest enough.")
        claims_legit = False
    
    
    print("Enter the authentication phrase:")
    sample = significant(
        next(get_readings_for(win_read_cli, times=1, auth_phrase=model.auth_phrase))
    )


    sample_e = expectile(sample)
    sample_d = dispersion(sample)

    logging.info(
        "Reference parameters: %s. Sample: (%s, %s)",
        model.references,
        sample_e,
        sample_d,
    )

    success = 0
    failure = 0
    for ref in model.references:
        if match(
            (ref.expectile, ref.variation), (sample_e, sample_d), len(model.auth_phrase)
        ):
            success += 1
        else:
            failure += 1

    p = success / (success + failure)

    logger.info("Sample match against stored model: %.2f%%", p * 100)

    if p >= update_threshold:
        logger.debug("Expanding stored model with a new sample")
        ms.update_model(username, Reference(expectile=sample_e, variation=sample_d))

    authed = p >= threshold
    ms.update_stats(
        username,
        claims_legit=claims_legit,
        result=(LoginResult.Accepted if authed else LoginResult.Rejected),
    )

    return authed


def main():
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        "--a2",
        type=float,
        default=0.05,
        help="homogeneous dispersion hypothesis criteria level",
    )
    argparser.add_argument(
        "--a3",
        type=float,
        default=0.05,
        help="distribution center equality hypothesis criteria level",
    )
    argparser.add_argument(
        "--p_a", type=float, default=0.85, help="successful authentication threshold"
    )
    argparser.add_argument(
        "--p_u", type=float, default=0.85, help="update model with sample threshold"
    )
    argparser.add_argument(
        "-v", action="count", default=0, help="verbosity (-vv for debug)"
    )

    arguments = argparser.parse_args()

    if arguments.v == 0:
        logging.basicConfig(level=logging.ERROR)
    elif arguments.v == 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    ms = Storage("db.db")
    match input(f"Choose operation mode ({Mode.help()}): ").upper():
        case Mode.Authenticate:
            authresult = authenticate(
                ms,
                a2=arguments.a2,
                a3=arguments.a3,
                threshold=arguments.p_a,
                update_threshold=arguments.p_u,
            )

            if authresult:
                print("[+] AUTHENTICATION SUCCESSFUL")
            else:
                print("[-] AUTHENTICATION FAILED")

            print(f"[=] FAR: {ms.get_far() * 100:.2f}%")
            print(f"[=] FRR: {ms.get_frr() * 100:.2f}%")

        case Mode.Learn:
            learn(ms)


if __name__ == "__main__":
    main()
