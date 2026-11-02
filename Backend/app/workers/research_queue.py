"""Run a bounded batch from the durable local queue, using a scoped service account."""
import argparse
from ..database import SessionLocal
from ..repositories.identity import UserRepository
from ..services.tasks import run_one,fail_stale


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service-user-id',type=int,required=True)
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--recover-stale',action='store_true')
    args=parser.parse_args()
    if not 1<=args.limit<=200:
        parser.error('--limit doit être compris entre 1 et 200.')
    with SessionLocal() as db:
        user=UserRepository(db).get_for_auth(args.service_user_id)
        if user is None or user.account_type!='service':
            parser.error('Un compte SERVICE_IA actif avec tasks.run et research.run est requis.')
        if args.recover_stale:
            print('Tâches interrompues marquées en échec :',fail_stale(db,user))
        processed=0
        for _ in range(args.limit):
            job=run_one(db,user)
            if job is None:
                break
            processed+=1
            print('task_id=',job.id,'status=',job.statut)
        print('Tâches traitées :',processed)


if __name__=='__main__':
    main()
