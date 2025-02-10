def generateNginxConfig(proxyValues) {
    def nginxConfig = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: default
data:
  nginx.conf: |
    http {
        server {
            listen 80;
"""

    // Define exact path-to-origin mapping
    def specialPaths = [
        "/digital/nsa/nos/ui/payment"    : "chatbot-exp.verizon.com",
        "/Mobile/nsa/nos/ui/webpunchout" : "www.verizon.com",
        "/soe/digital/prospect/"         : "secure.verizon.com"
    ]

    proxyValues.each { color, paths ->
        paths.each { pathEntry ->
            def path = pathEntry.path
            def proxyPass = pathEntry.url

            nginxConfig += """
            location ${path} {
                proxy_pass ${proxyPass};
"""

            // Check for an exact match in specialPaths
            if (specialPaths.containsKey(path)) {
                def origin = specialPaths[path]
                nginxConfig += """
                if (\$request_method = 'OPTIONS') {
                    add_header 'Access-Control-Allow-Origin' '${origin}';
                    add_header 'Access-Control-Allow-Credentials' 'true';
                    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                    add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type';
                }
"""
            }

            nginxConfig += "            }\n"
        }
    }

    nginxConfig += "        }\n    }\n"
    return nginxConfig
}


def generateNginxConfig(proxyValues) {
    def nginxConfig = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: default
data:
  nginx.conf: |
    http {
        server {
            listen 80;
"""

    // Define exact path-to-origin mapping
    def specialPaths = [
        "/digital/nsa/nos/ui/payment"    : "chatbot-exp.verizon.com",
        "/Mobile/nsa/nos/ui/webpunchout" : "www.verizon.com",
        "/soe/digital/prospect/"         : "secure.verizon.com"
    ]

    proxyValues.each { color, paths ->
        paths.each { pathEntry ->
            def path = pathEntry.path
            def proxyPass = pathEntry.url

            nginxConfig += """
            location ${path} {
                proxy_pass ${proxyPass};
"""

            // Check for an exact match in specialPaths
            if (specialPaths.containsKey(path)) {
                def origin = specialPaths[path]
                nginxConfig += """
                if (\$request_method = 'OPTIONS') {
                    add_header 'Access-Control-Allow-Origin' '${origin}';
                    add_header 'Access-Control-Allow-Credentials' 'true';
                    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
                    add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type';
                }
"""
            }

            nginxConfig += "            }\n"
        }
    }

    nginxConfig += "        }\n    }\n"
    return nginxConfig
}



def generateIngressYaml(values, subenv) {
    def ingress = """
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
"""
    // Add ALB conditions based on the subenv
    def vsad = values.global.project.vsad.toLowerCase()
    switch (subenv) {
        case 'dit':
            ingress += """
  annotations:
    alb.ingress.kubernetes.io/conditions.${vsad}-nginx-green-svc: |
      [{"field":"http-header","httpHeaderConfig":{"httpHeaderName":"x-canary","values":["true"]}}]
"""
            break
        case 'sit':
            ingress += """
  annotations:
    alb.ingress.kubernetes.io/conditions.${vsad}-nginx-green-svc: |
      [{"field":"http-header","httpHeaderConfig":{"httpHeaderName":"x-canary","values":["true"]}}]
    alb.ingress.kubernetes.io/conditions.${vsad}-nginx-blue-svc: |
      [{"field":"http-header","httpHeaderConfig":{"httpHeaderName":"x-sit","values":["true"]}}]
"""
            break
        case 'prod':
            ingress += """
  annotations:
    alb.ingress.kubernetes.io/conditions.${vsad}-nginx-green-svc: |
      [{"field":"http-header","httpHeaderConfig":{"httpHeaderName":"x-canary","values":["true"]}}]
    alb.ingress.kubernetes.io/conditions.${vsad}-nginx-blue-svc: |
      [{"field":"http-header","httpHeaderConfig":{"httpHeaderName":"x-prod","values":["true"]}}]
    alb.ingress.kubernetes.io/conditions.${vsad}-nginx-prod-svc: |
      [{"field":"http-header","httpHeaderConfig":{"httpHeaderName":"x-prod","values":["true"]}}]
"""
            break
    }

    ingress += "spec:\n  rules:\n"
    values.Proxy_values.each { color, paths ->
        paths.each { path ->
            ingress += """
    - host: ${values.global.host ?: 'example.com'}
      http:
        paths:
          - path: ${path.path}
            pathType: Prefix
            backend:
              service:
                name: nginx-${color}-svc
                port:
                  number: 80
"""
        }
    }
    return ingress
}

// Example usage within a Jenkins pipeline
pipeline {
    agent any

    environment {
        HELM_HOME = '/path/to/helm/home'
    }

    stages {
        stage('Deploy Nginx Blue') {
            steps {
                script {
                    sh "helm upgrade --install nginx-blue /path/to/nginx-blue/chart --values /path/to/values.yaml"
                }
            }
        }

        stage('Deploy Nginx Green') {
            steps {
                script {
                    sh "helm upgrade --install nginx-green /path/to/nginx-green/chart --values /path/to/values.yaml"
                }
            }
        }

        stage('Create Ingress') {
            steps {
                script {
                    // Read the input YAML file content
                    def inputFilePath = 'path/to/your/values.yaml'
                    def fileContent = readFile(inputFilePath)
                    
                    // Parse the YAML content
                    def values = new YamlSlurper().parseText(fileContent)
                    
                    // Define subenv
                    def subenv = values.subenv ?: 'default'

                    // Generate the Ingress YAML
                    def ingressYaml = generateIngressYaml(values, subenv)

                    // Write the generated Ingress YAML to a file
                    def outputFilePath = 'ingress.yaml'
                    writeFile file: outputFilePath, text: ingressYaml

                    // Apply the Ingress configuration using kubectl
                    sh "kubectl apply -f ${outputFilePath}"
                }
            }
        }
    }
}
