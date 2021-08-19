import logging

import falcon
from falcon_cors import CORS

logging.basicConfig(level=logging.INFO)

from open_source.rest import parlours, plans

cors = CORS(allow_all_origins=True, allow_all_methods=True, allow_all_headers=True)

api = falcon.App(middleware=cors.middleware)

api.add_route('/open-source/parlour/', parlours.ParlourGetAllEndpoint())
api.add_route('/open-source/parlour', parlours.ParlourPostEndpoint())
api.add_route('/open-source/parlour/{id}', parlours.ParlourGetEndpoint())
api.add_route('/open-source/parlour/{id}/update', parlours.ParlourPutEndpoint())
api.add_route('/open-source/parlour/{id}/delete', parlours.ParlourDeleteEndpoint())
api.add_route('/open-source/plan/', plans.PlanGetAllEndpoint())



# api.add_route('/payment-service/swagger.json', swagger.SwaggerHandler())


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8009, api)
    httpd.serve_forever()
