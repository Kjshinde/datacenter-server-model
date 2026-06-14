classdef load_dvfs_callback_1
% This class contains static methods for Simulink mask callbacks
% to load and save DVFS table parameters to/from a .csv file.

    methods(Static)

        %% --- LOAD MASK PARAMETERS FROM CSV ---
        % Callback for the 'load_dvfs_button'
        function load_dvfs_button(~)
            [file, path] = uigetfile('*.csv', 'Select a DVFS Profile');
            
            % Check if the user selected a file
            if ischar(file)
                try
                    % Detect import options and force string type for reliability
                    opts = detectImportOptions(fullfile(path, file));
                    opts = setvartype(opts, {'Parameter', 'Value'}, 'string');
                    T = readtable(fullfile(path, file), opts);
                    
                    % Get all available parameter names from the current block
                    availableParams = get_param(gcb, 'MaskNames');
                    
                    % Loop through each row in the loaded CSV
                    for i = 1:height(T)
                        % Safely extract parameter name
                        if iscell(T.Parameter)
                            paramName = T.Parameter{i};
                        else
                            paramName = T.Parameter(i);
                        end
                        paramName = char(paramName); % ensure character vector
                        
                        % Safely extract parameter value
                        if iscell(T.Value)
                            valueFromCell = T.Value{i};
                        else
                            valueFromCell = T.Value(i);
                        end
                        
                        % Convert value to string form for Simulink
                        if isnumeric(valueFromCell)
                            paramValue = num2str(valueFromCell);
                        else
                            paramValue = char(string(valueFromCell));
                        end
                        
                        % Only set existing parameters
                        if any(strcmp(availableParams, paramName))
                            set_param(gcb, paramName, paramValue);
                        else
                            warning('Skipping parameter "%s" as it does not exist on this mask.', paramName);
                        end
                    end
                    
                    msgbox(['Parameters loaded from: ' file], 'Success');
                    
                catch ME
                    errordlg(['Failed to load file. Error: ' ME.message], 'Error');
                end
            else
                disp('Load operation cancelled.');
            end    
        end


        %% --- SAVE MASK PARAMETERS TO CSV ---
        % Callback for the 'save_dvfs_button'
        function save_dvfs_button(~)
            try
                % Get all mask parameter names
                allParamNames = get_param(gcb, 'MaskNames');
                
                % Parameters to exclude from saving
                paramsToExclude = {
                    'DescGroupVar', ...
                    'DescTextVar', ...
                    'ParameterGroupVar', ...
                    'save_dvfs_button', ...
                    'load_dvfs_button'
                };
                
                % Keep only the relevant parameters
                paramNamesToSave = setdiff(allParamNames, paramsToExclude, 'stable');
                
                % Get current values
                paramValues = cell(length(paramNamesToSave), 1);
                for i = 1:length(paramNamesToSave)
                    paramValues{i} = get_param(gcb, paramNamesToSave{i});
                end
                
                % Create table
                T = table(paramNamesToSave, paramValues, ...
                    'VariableNames', {'Parameter', 'Value'});
                
                % Ask user for save location
                [file, path] = uiputfile('*.csv', 'Save DVFS Profile As');
                
                % Save only if user confirmed
                if ischar(file)
                    writetable(T, fullfile(path, file));
                    msgbox(['Parameters saved to: ' file], 'Success');
                else
                    disp('Save operation cancelled.');
                end
            catch ME
                errordlg(['Failed to save file. Error: ' ME.message], 'Error');
            end
        end

    end
end
