classdef load_callback

    methods(Static) % testing CCs commit (14 sep) 

        % Use the code browser on the left to add the callbacks.


        function saveButton(~)
        % --- SAVE MASK PARAMETERS TO CSV ---
    
    % List of parameter names from your mask
    paramNames = {
        'Init_core'; 'Init_uti'; 'Init_inst'; ...
        'Comp_core'; 'Comp_uti'; 'Comp_inst'; ...
        'Result_core'; 'Result_uti'; 'Result_inst';...
        'Main_inst_scale'
    };
    
    % Get current values from the mask
    paramValues = zeros(length(paramNames), 1);
    for i = 1:length(paramNames)
        % get_param gets the value of a parameter from the current block ('gcb')
        paramValues(i) = str2double(get_param(gcb, paramNames{i}));
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
    

        function loadButton(~)
% Ask user to select a CSV file
[file, path] = uigetfile('*.csv', 'Select a Compute Load Profile');

% If the user selected a file, read it and set the parameters
if ischar(file)
    try
        T = readtable(fullfile(path, file));
        
        % Loop through each parameter in the table and update the mask
        for i = 1:height(T)
            paramName = T.Parameter{i};
            paramValue = num2str(T.Value(i));
            
            % set_param sets the value of a parameter on the current block ('gcb')
            set_param(gcb, paramName, paramValue);
        end
        
        msgbox(['Parameters loaded from: ' file], 'Success');
        
    catch ME
        errordlg(['Failed to load file. Error: ' ME.message], 'Error');
    end
else
    disp('Load operation cancelled.');
end            
        end
        end
end