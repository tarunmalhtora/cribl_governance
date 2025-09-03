pipeline {
   agent any  // Run on any available Jenkins agent

    // ---------- Parameters defined for user input ----------
    parameters {
        choice(name: 'env', choices: ['Cribl Dev','Cribl NonProd','Cribl Prod'], description: 'Environment')
        string(name: 'routeName', defaultValue: '', description: 'Route Name', trim: true)
        string(name: 'filter', defaultValue: '', description: 'Filter condition for route', trim: true)
        string(name: 'pipelineName', defaultValue: '', description: 'Pipeline Name in Cribl', trim: true)
        choice(name: 'destination', choices: [
            'splunk-idx-prod',
            'OpenSearch-Auto-dev',
            'OpenSearch-Auto-sit',
            'OpenSearch-Auto-prod'
        ], description: 'Destination system')
        booleanParam(name: 'finalFlag', defaultValue: false, description: 'Final flag for route')
        text(name: 'description', defaultValue: '', description: 'Description / notes for this route')
        string(name: 'role', defaultValue: 'dev', description: 'Role from UI (dev/sre)', trim: true)
    }

    stages {

        // ---------- Stage 1: Print all user inputs ----------
        stage('Echo Inputs') {
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
        // ---------- Stage 2: Route Validation Logic ----------
        stage('Route Validation Checks') {
            steps {
                script {
                    // Build unique filenames for this run (BUILD_ID = Jenkins build number)
                    def inputFile  = "routes_${env.BUILD_ID}.json"
                    def reportFile = "validation_report_${env.BUILD_ID}.json"

                    // Write JSON payload with route information
                    def routeJson = """
                    [
                      {
                        "name": "${params.routeName}",
                        "destination": "${params.destination}",
                        "filter": "${params.filter}",
                        "finalFlag": ${params.finalFlag}
                      }
                    ]
                    """
                   //Take the text stored in the variable routeJson and write it into a new file named whatever is in the inputFile variable."
                    writeFile file: inputFile, text: routeJson 

                    // 🔍 Debugging before running Python
                    sh "echo '🔍 Debug Info:'"
                    sh "which python3 || true"
                    sh "python3 --version || true"
                    sh "ls -l"
                    sh "cat ${inputFile}"

                    // Run Python validation script and capture exit code
                    def pyExitCode = sh(script: "python3 route_validator.py ${inputFile} > ${reportFile}", returnStatus: true)

                    // Show raw report for debugging
                    echo "📋 Raw validation report (JSON):"
                    sh "cat ${reportFile} || echo '⚠️ No report file created'"

                    if (pyExitCode != 0) {
                        error("Fatal error running validation script (exit code: ${pyExitCode}).")
                    }

                    // Parse JSON report file into Groovy object
                    def report = readJSON file: reportFile

                    // Iterate over each route in the report
                    report.each { routeResult ->
                        echo "Route '${routeResult.route_name}': ${routeResult.is_valid ? '✅ VALID' : '❌ INVALID'}"
                        routeResult.errors?.each { err ->
                            echo "     - [ERROR] ${err}"
                        }
                        routeResult.warnings?.each { warn ->
                            echo "     - [WARN]  ${warn}"
                        }
                    }

                    // Archive JSON report as artifact for history
                    archiveArtifacts artifacts: reportFile, onlyIfSuccessful: false
                }
            }
        }
    }

    // ---------- Post build actions ----------
    post {
        always {
            echo "🧹 Cleaning up workspace files"
            cleanWs()  // Deletes all workspace files after archiving
        }
        failure {
            echo "❌ Route validation failed. Please check the logs above."
        }
        success {
            echo "✅ Route validation passed successfully!"
        }
    }
}
