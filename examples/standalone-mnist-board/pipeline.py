import numpy as np

from fedlab.board import fedboard
from fedlab.core.standalone import StandalonePipeline


class ExamplePipeline(StandalonePipeline):

    def main(self):
        round = 0
        while self.handler.if_stop is False:
            # server side
            sampled_clients = self.handler.sample_clients(self.trainer.num_clients)
            broadcast = self.handler.downlink_package

            # client side
            self.trainer.local_process(broadcast, sampled_clients)
            uploads = self.trainer.uplink_package

            # server side
            for pack in uploads:
                self.handler.load(pack)

            # evaluate and log the result to FedBoard
            losses = self.evaluate()
            overall_loss = np.average([l for l in losses.values()])
            metrics = {'loss': overall_loss, 'nlosss': -overall_loss}
            client_metrics = {str(id): {'loss': ls, 'nloss': -ls} for id, ls in losses.items()}
            fedboard.log(round + 1,
                         metrics=metrics, main_metric_name='loss', client_metrics=client_metrics,
                         client_params={str(id): pack[0] for id, pack in enumerate(uploads)}, )
            round += 1

    def evaluate(self):
        return self.trainer.get_loss()
