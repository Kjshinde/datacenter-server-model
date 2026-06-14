classdef proc_config_load_store

    methods(Static)

        % --- LOAD MASK PARAMETERS FROM CSV ---
        % This function is already generic and correct.
        function load_button(~)
            [file, path] = uigetfile('*.csv', 'Select a Compute Load Profile');
            if ischar(file)
                try
                    T = readtable(fullfile(path, file));
                    
                    % Get all available parameter names from the current block
                    % This avoids errors if the CSV has extra parameters
                    availableParams = get_param(gcb, 'MaskNames');
                    
                    for i = 1:height(T)
                        paramName = T.Parameter{i};
                        paramValue = num2str(T.Value(i));
                        
                        % Only set the parameter if it actually exists on this mask
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


        % --- SAVE MASK PARAMETERS TO CSV ---
        % This is the NEW, GENERIC version that works for any mask
        function save_button(~)
            
            % Get all workspace variables from the current mask
            % This returns a struct (e.g., s.Tj_max=95, s.TDP=350, etc.)
            maskVars = get_param(gcb, 'MaskWSVariables');
            
            % Get the parameter names from the struct
            % This will get 'F_cpu' on the CPU block and 'F_gpu' on the GPU block
            paramNames = fieldnames(maskVars);
            
            % Get current values from the struct
            paramValues = cell(length(paramNames), 1);
            for i = 1:length(paramNames)
                % Get the value corresponding to the parameter name
                paramValues{i} = maskVars.(paramNames{i});
            end
            
            % Create a table to hold the data
            T = table(paramNames, paramValues, 'VariableNames', {'Parameter', 'Value'});
            
            % Ask user where to save the file
            [file, path] = uiputfile('*.csv', 'Save Compute Load Profile As');
            
            % If the user selected a file, write the table to CSV
            if ischar(file)
                writetable(T, fullfile(path, file));
                msgbox(['Parameters saved to: ' file], 'Success');
            else
                disp('Save operation cancelled.');
            end
        end

    end
end