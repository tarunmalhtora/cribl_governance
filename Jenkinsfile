pipeline {
  agent any
  parameters {
    // match your UI fields
    choice(name: 'env', choices: ['Cribl Dev','Cribl NonProd','Cribl Prod'], description: 'Environment')
    string(name: 'routeName', defaultValue: '', description: 'Route Name', trim: true)
    string(name: 'filter', defaultValue: '', description: 'Filter', trim: true)
    string(name: 'pipelineName', defaultValue: '', description: 'Pipeline Name', trim: true)
    choice(name: 'destination', choices: [
      'splunk-idx-prod',
      'OpenSearch-Auto-dev',
      'OpenSearch-Auto-sit',
      'OpenSearch-Auto-prod'
    ], description: 'Destination')
    booleanParam(name: 'finalFlag', defaultValue: false, description: 'Final flag')
    text(name: 'description', defaultValue: '', description: 'Description / notes')
    string(name: 'role', defaultValue: 'dev', description: 'Role from UI (dev/sre)', trim: true)
  }

  stages {
    stage('Echo Inputs from UI Route Validator') {
      steps {
        echo """
        --- Route Validation Inputs ---
        role        = ${params.role}
        env         = ${params.env}
        routeName   = ${params.routeName}
        filter      = ${params.filter}
        pipelineName= ${params.pipelineName}
        destination = ${params.destination}
        finalFlag   = ${params.finalFlag}
        description = ${params.description}
        --------------------------------
        """
      }
    }

    stage('Route Naming Convention Validation') {
      steps {
        script {
          // Create a temporary JSON file from Jenkins parameters
          def routeJson = """
          [
            {
              "name": "${params.routeName}",
              "destination": "${params.destination}"
            }
          ]
          """
          writeFile file: 'routes.json', text: routeJson

          // Run Python script directly and print results into Jenkins logs
          sh '''
            echo "Running Python validation..."
            python3 route_validator.py routes.json
          '''
        }
      }
    }
  }
}
